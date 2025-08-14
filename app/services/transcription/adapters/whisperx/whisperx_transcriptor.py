# app/services/transcription/adapters/whisperx_t.py
from __future__ import annotations
import whisperx
from typing import Optional
from app.ports.services.transcription import Transcriber, TranscriptionSegmentInput

class WhisperXTranscriber(Transcriber):
    def __init__(self, *, device: str, model_size: str, compute_type: str, hf_token: str):
        self.device = device
        self.model = whisperx.load_model(model_size, device, compute_type=compute_type)
        self.hf_token = hf_token

    def transcribe_blob(self, container: str, blob: str, *, locale: Optional[str] = None, speaker_diarization: bool = True) -> list[TranscriptionSegmentInput]:
        raise NotImplementedError

    def transcribe_file(self, path: str, *, locale: Optional[str] = None, speaker_diarization: bool = True) -> list[TranscriptionSegmentInput]:
        audio = whisperx.load_audio(path)
        result = self.model.transcribe(audio, batch_size=8)
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, self.device, return_char_alignments=False)
        if speaker_diarization:
            diar = whisperx.diarize.DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)
            diar_segments = diar(audio)
            result = whisperx.assign_word_speakers(diar_segments, result)

        out: list[TranscriptionSegmentInput] = []
        for s in result["segments"]:
            out.append({
                "speaker": s.get("speaker", "?"),
                "text": s["text"],
                "start_time": round(s["start"], 2),
                "end_time": round(s["end"], 2),
            })
        return out

