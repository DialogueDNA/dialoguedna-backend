from __future__ import annotations
import whisperx

from app.core.config.providers.whisperx import WhisperXConfig
from app.ports.services.transcription import Transcriber, TranscriptionSegmentInput, TranscriptionSegmentOutput


class WhisperXTranscriber(Transcriber):
    def __init__(self, cfg: WhisperXConfig):
        self.device = cfg.device
        self.model = whisperx.load_model(cfg.model_size, cfg.device, compute_type=cfg.compute_type)
        self.hf_token = cfg.hf_token

    def transcribe(self, segment: TranscriptionSegmentInput) -> TranscriptionSegmentOutput:
        raise NotImplementedError

