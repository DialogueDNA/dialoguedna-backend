from __future__ import annotations

import io, wave, tempfile, json
from dataclasses import dataclass
from typing import Any, Optional, List, Dict

import numpy as np
import requests
import torch

from app.core.config.providers.azure.speech_to_text import AzureSpeechToTextConfig
from app.interfaces.services.transcription import (
    Transcriber, TranscriptionInput, TranscriptionOutput,
)
from app.interfaces.services.text import TextSegment
from app.interfaces.services.audio import AudioSegment

FAST_API_VERSION = "2024-11-15"
_SHORT_TIMEOUT = 60
_FAST_TIMEOUT  = 300

@dataclass
class _WavBlob:
    path: Optional[str]
    bytes_io: Optional[io.BytesIO]
    sample_rate: int

class AzureSpeechToTextTranscriber(Transcriber):
    def __init__(self, cfg: AzureSpeechToTextConfig):
        self._cfg = cfg
        self._key = cfg.key
        self._region = cfg.region
        self._locale = cfg.locale or "en-US"
        self._default_diar = bool(cfg.speaker_diarization)

    def transcribe(self, segment: TranscriptionInput) -> TranscriptionOutput:
        audio: AudioSegment = segment.audio
        want_diar = bool(segment.diarization if segment.diarization is not None else self._default_diar)

        wav = self._ensure_wav(audio)

        if want_diar and self._cfg.use_fast_when_diarization:
            return self._recognize_fast_with_diarization(wav)
        else:
            text = self._recognize_short_audio(wav)
            return [TextSegment(
                writer=audio.speaker, text=text or "",
                start_time=audio.start_time, end_time=audio.end_time, language=self._locale
            )]

    # ---------- Fast Transcription ----------
    def _recognize_fast_with_diarization(self, wav: _WavBlob) -> List[TextSegment]:

        url = f"https://{self._region}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe"
        params = {"api-version": FAST_API_VERSION}

        if wav.path:
            with open(wav.path, "rb") as f:
                audio_bytes = f.read()
        else:
            audio_bytes = wav.bytes_io.getvalue() if wav.bytes_io else b""

        definition = {
            "locales": [self._locale],
            "diarization": {"enabled": True},
        }
        if self._cfg.max_speakers and self._cfg.max_speakers > 0:
            definition["diarization"]["maxSpeakers"] = int(self._cfg.max_speakers)

        files = {
            "audio": ("audio.wav", audio_bytes, "audio/wav"),
            "definition": (None, json.dumps(definition), "application/json"),
        }
        headers = {"Ocp-Apim-Subscription-Key": self._key}

        r = requests.post(url, params=params, headers=headers, files=files, timeout=_FAST_TIMEOUT)
        r.raise_for_status()
        payload: Dict[str, Any] = r.json()

        phrases = payload.get("phrases") or []
        out: List[TextSegment] = []
        for ph in phrases:
            txt = (ph.get("text") or "").strip()
            if not txt:
                continue
            off_ms = float(ph.get("offsetMilliseconds") or 0.0)
            dur_ms = float(ph.get("durationMilliseconds") or 0.0)
            spk = ph.get("speaker") or ph.get("speakerId")
            seg = TextSegment(
                writer=spk if isinstance(spk, (int, str)) else None,
                text=txt,
                start_time=off_ms / 1000.0,
                end_time=(off_ms + dur_ms) / 1000.0 if dur_ms else None,
                language=(ph.get("locale") or self._locale),
            )
            out.append(seg)

        if not out:
            comb = payload.get("combinedPhrases") or []
            combined_text = " ".join((it.get("text") or "").strip() for it in comb if it.get("text"))
            if combined_text:
                out = [TextSegment(writer=None, text=combined_text, start_time=None, end_time=None, language=self._locale)]
        return out

    # ---------- Short Audio ----------
    def _recognize_short_audio(self, wav: _WavBlob) -> str:
        url = f"https://{self._region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        params = {"language": self._locale}
        headers = {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": f"audio/wav; codecs=audio/pcm; samplerate={wav.sample_rate}",
        }
        if wav.path:
            with open(wav.path, "rb") as f:
                data = f.read()
        else:
            data = wav.bytes_io.getvalue() if wav.bytes_io else b""
        r = requests.post(url, params=params, headers=headers, data=data, timeout=_SHORT_TIMEOUT)
        r.raise_for_status()
        payload: Dict[str, Any] = r.json()
        return str(payload.get("DisplayText") or "")

    def _ensure_wav(self, audio: AudioSegment, target_sr: int = 16_000) -> _WavBlob:
        obj = audio.audio
        if isinstance(obj, torch.Tensor):
            wf = obj.detach().cpu()
            if wf.dim() == 1: wf = wf.unsqueeze(0)
            if wf.size(0) > 1: wf = wf.mean(dim=0, keepdim=True)
            sr = int(audio.sample_rate or target_sr)
            if sr != target_sr:
                wf = self._resample_torch(wf, sr, target_sr); sr = target_sr
            pcm16 = self._float_to_pcm16(wf.squeeze(0).numpy())
            bio = io.BytesIO()
            with wave.open(bio, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                w.writeframes(pcm16.tobytes())
            bio.seek(0)
            return _WavBlob(path=None, bytes_io=bio, sample_rate=sr)

        path = str(obj)
        try:
            with wave.open(path, "rb") as w:
                ch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getframerate()
            if ch == 1 and sw == 2 and fr == target_sr:
                return _WavBlob(path=path, bytes_io=None, sample_rate=fr)
        except wave.Error:
            pass

        try:
            with wave.open(path, "rb") as w:
                frames, fr, ch, sw = w.readframes(w.getnframes()), w.getframerate(), w.getnchannels(), w.getsampwidth()
            dtype = np.int16 if sw == 2 else np.int16
            data = np.frombuffer(frames, dtype=dtype)
            if ch > 1: data = data.reshape(-1, ch).mean(axis=1).astype(np.int16)
            wf = torch.from_numpy((data.astype(np.float32) / 32768.0)).unsqueeze(0)
        except Exception:
            try:
                import librosa
                y, sr0 = librosa.load(path, sr=None, mono=True)
                wf = torch.from_numpy(y.astype(np.float32)).unsqueeze(0); fr = int(sr0)
            except Exception as e:
                raise RuntimeError(f"Unsupported audio file for Short/Fast Audio path: {path}") from e

        if fr != target_sr:
            wf = self._resample_torch(wf, fr, target_sr)
        pcm16 = self._float_to_pcm16(wf.squeeze(0).numpy())
        tmp = tempfile.NamedTemporaryFile(prefix="stt_", suffix=".wav", delete=False); tmp.close()
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(target_sr)
            w.writeframes(pcm16.tobytes())
        return _WavBlob(path=tmp.name, bytes_io=None, sample_rate=target_sr)

    @staticmethod
    def _resample_torch(wf: torch.Tensor, src_sr: int, dst_sr: int) -> torch.Tensor:
        assert wf.dim() == 2 and wf.size(0) == 1, "expected mono [1, T]"
        T_src = wf.size(1)
        T_dst = max(int(round(T_src * (dst_sr / float(src_sr)))), 1)
        x_src = torch.linspace(0.0, 1.0, steps=T_src, dtype=wf.dtype)
        x_dst = torch.linspace(0.0, 1.0, steps=T_dst, dtype=wf.dtype)
        out = torch.interp(x_dst, x_src, wf[0])
        return out.unsqueeze(0)

    @staticmethod
    def _float_to_pcm16(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -1.0, 1.0)
        return (x * 32767.0).astype(np.int16)
