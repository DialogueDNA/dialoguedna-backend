# audio_pipeline/diarizer.py

import torch
import whisperx
from .config import DEFAULT_MODEL_SIZE, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE, BATCH_SIZE
from .base import DiarizationResult
from app.core.environment import HUGGINGFACE_WHISPERX_TOKEN


class Diarizer:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.device = DEFAULT_DEVICE if torch.cuda.is_available() else "cpu"
        self.compute_type = DEFAULT_COMPUTE_TYPE if self.device == "cuda" else "float32"
        self.model = whisperx.load_model(DEFAULT_MODEL_SIZE, self.device, compute_type=self.compute_type)

    def run(self) -> DiarizationResult:
        print("[Diarizer] Transcribing...")
        transcription = self.model.transcribe(self.audio_path, batch_size=BATCH_SIZE)

        print("[Diarizer] Running diarization...")
        diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=HUGGINGFACE_WHISPERX_TOKEN, device=self.device)
        diarization_segments = diarize_model(self.audio_path)

        print("[Diarizer] Aligning transcription with speakers...")
        aligned_segments = whisperx.diarize.align_with_diarization(
            transcription["segments"],
            diarization_segments["segments"]
        )

        return DiarizationResult(aligned_segments)
