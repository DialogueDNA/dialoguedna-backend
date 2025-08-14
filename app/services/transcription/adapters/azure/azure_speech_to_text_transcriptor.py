from __future__ import annotations

import io
import wave
import tempfile
from dataclasses import dataclass
from typing import Optional

import numpy as np
import requests
import torch

from app.core.config.providers.azure.speech_to_text import AzureSpeechToTextConfig
from app.ports.services.transcription import (
    Transcriber,
    TranscriptionSegmentInput,
    TranscriptionSegmentOutput,  # = TextSegment
)
from app.ports.services.text import TextSegment
from app.ports.services.audio import AudioSegment  # dataclass עם audio: Union[path, torch.Tensor]


@dataclass
class _WavBlob:
    path: Optional[str]      # נתיב לקובץ על הדיסק (אם שמרנו), אחרת None
    bytes_io: Optional[io.BytesIO]  # אם כתבנו לזיכרון
    sample_rate: int


class AzureSpeechToTextTranscriber(Transcriber):
    """
    Transcriber המתאים לחתימות:
      __init__(cfg: AzureSpeechToTextConfig)
      transcribe(segment: TranscriptionSegmentInput) -> TranscriptionSegmentOutput (TextSegment)

    הערה: דיאריזציה מלאה קיימת אצל Azure בעיקר ב-Batch; כאן זה מסלול "Short Audio".
    השדה segment.diarization יותאם בהמשך לגרסאות Batch אם תצטרך/י.
    """

    def __init__(self, cfg: AzureSpeechToTextConfig):
        self._key = cfg.key
        self._region = cfg.region
        self._locale = cfg.locale or "en-US"
        self._default_diar = bool(cfg.speaker_diarization)

    # ---------------- Public API ----------------
    def transcribe(self, segment: TranscriptionSegmentInput) -> TranscriptionSegmentOutput:
        audio: AudioSegment = segment.audio
        diar_req = bool(segment.diarization if segment.diarization is not None else self._default_diar)

        # הכנה ל-WAV: קבל path או שמור טנזור זמנית, ודאג ל-PCM 16kHz mono
        wav = self._ensure_wav(audio)

        # מסלול Short Audio (שורת REST אחת; ללא דיאריזציה מלאה)
        text = self._recognize_short_audio(wav)

        # בונה TextSegment לפי הקונטרקט
        return TextSegment(
            writer=audio.speaker,                 # אם סופק רמקול מראש — נשמר
            text=text or "",
            start_time=audio.start_time,
            end_time=audio.end_time,
            language=self._locale,
        )

    # ---------------- Internals ----------------
    def _recognize_short_audio(self, wav: _WavBlob) -> str:
        """
        Azure Speech-to-Text REST (Short Audio).
        https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=...
        """
        url = f"https://{self._region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        params = {"language": self._locale}
        headers = {
            "Ocp-Apim-Subscription-Key": self._key,
            # 16kHz PCM; אם הזנו 16k בעיבוד — זה תואם
            "Content-Type": f"audio/wav; codecs=audio/pcm; samplerate={wav.sample_rate}",
        }

        # נשלח גוף הבקשה כ-binary (מהקובץ או מהזיכרון)
        if wav.path:
            with open(wav.path, "rb") as f:
                data = f.read()
        else:
            data = wav.bytes_io.getvalue() if wav.bytes_io else b""

        r = requests.post(url, params=params, headers=headers, data=data, timeout=60)
        r.raise_for_status()
        payload = r.json()

        # התשובה מכילה לרוב DisplayText/RecognitionStatus
        # דוגמא: {"RecognitionStatus":"Success","DisplayText":"hello world","Duration":...,"Offset":...}
        return str(payload.get("DisplayText") or "")

    # עזר: קבלת WAV ב-16kHz מ-path או מטנזור
    def _ensure_wav(self, audio: AudioSegment, target_sr: int = 16_000) -> _WavBlob:
        obj = audio.audio
        if isinstance(obj, torch.Tensor):
            # צפוי float [-1,1], צורה [C,T] או [T]
            wf = obj.detach().cpu()
            if wf.dim() == 1:
                wf = wf.unsqueeze(0)
            # ממוצע לערוץ יחיד
            if wf.size(0) > 1:
                wf = wf.mean(dim=0, keepdim=True)
            sr = int(audio.sample_rate or target_sr)
            # רסמפל ל-16k אם צריך (ליניארי ופשוט; די טוב לדיבור)
            if sr != target_sr:
                wf = self._resample_torch(wf, sr, target_sr)
                sr = target_sr
            # כתיבה לבאפר WAV בזיכרון (PCM16)
            pcm16 = self._float_to_pcm16(wf.squeeze(0).numpy())
            bio = io.BytesIO()
            with wave.open(bio, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)  # 16-bit
                w.setframerate(sr)
                w.writeframes(pcm16.tobytes())
            bio.seek(0)
            return _WavBlob(path=None, bytes_io=bio, sample_rate=sr)

        # אם זה path — דואגים שהוא ב־PCM16/16kHz; אם לא, נטען, נתקן, ונשמור לקובץ זמני.
        path = str(obj)
        with wave.open(path, "rb") as w:
            ch = w.getnchannels()
            sw = w.getsampwidth()
            fr = w.getframerate()
        if ch == 1 and sw == 2 and fr == target_sr:
            return _WavBlob(path=path, bytes_io=None, sample_rate=fr)

        # המרה: נטען בעזרת wave+numpy, נהפוך ל־float, נבצע downmix+resample ונשמור זמנית
        with wave.open(path, "rb") as w:
            frames = w.readframes(w.getnframes())
            fr = w.getframerate()
            ch = w.getnchannels()
            sw = w.getsampwidth()
        # תמיכה בסיסית ל-16bit בלבד; אם sw!=2, ננסה להמיר כמיטב יכולתנו
        dtype = np.int16 if sw == 2 else np.int16
        data = np.frombuffer(frames, dtype=dtype)
        if ch > 1:
            data = data.reshape(-1, ch).mean(axis=1).astype(np.int16)
        # ל-float[-1,1]
        wf = torch.from_numpy((data.astype(np.float32) / 32768.0)).unsqueeze(0)
        if fr != target_sr:
            wf = self._resample_torch(wf, fr, target_sr)
        pcm16 = self._float_to_pcm16(wf.squeeze(0).numpy())

        tmp = tempfile.NamedTemporaryFile(prefix="stt_", suffix=".wav", delete=False)
        tmp.close()
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(target_sr)
            w.writeframes(pcm16.tobytes())
        return _WavBlob(path=tmp.name, bytes_io=None, sample_rate=target_sr)

    @staticmethod
    def _resample_torch(wf: torch.Tensor, src_sr: int, dst_sr: int) -> torch.Tensor:
        """רסמפל לינארי פשוט [1,T] -> [1,T’] (דיבור)."""
        assert wf.dim() == 2 and wf.size(0) == 1, "expected mono [1, T]"
        T_src = wf.size(1)
        T_dst = max(int(round(T_src * (dst_sr / float(src_sr)))), 1)
        x_src = torch.linspace(0.0, 1.0, steps=T_src, dtype=wf.dtype)
        x_dst = torch.linspace(0.0, 1.0, steps=T_dst, dtype=wf.dtype)
        out = torch.interp(x_dst, x_src, wf[0])
        return out.unsqueeze(0)

    @staticmethod
    def _float_to_pcm16(x: np.ndarray) -> np.ndarray:
        """המרת float[-1,1] ל־int16 עם קליפינג עדין."""
        x = np.clip(x, -1.0, 1.0)
        return (x * 32767.0).astype(np.int16)
