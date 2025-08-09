# app/services/transcription/factory.py
from __future__ import annotations
from typing import Literal, Any

from app.services.transcription.transcriber import Transcriber
from app.services.transcription.models.azure_stt_transcriber import AzureSpeechTranscriber
from app.services.transcription.models.whisperx_transcriber import WhisperXTranscriber

BackendName = Literal["azure", "whisperx"]

def make_transcriber(backend: BackendName, **kwargs: Any) -> Transcriber:
    if backend == "azure":
        strategy = AzureSpeechTranscriber(**kwargs)
    elif backend == "whisperx":
        strategy = WhisperXTranscriber(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")
    return Transcriber(strategy)

# ---- Example usage ------------------------------------------------------------
# from app.services.transcription.factory import make_transcriber
#
# # Azure Speech-to-Text
# t1 = make_transcriber("azure", locale="en-US", diarization_enabled=True)
# lines = t1.transcribe("container/path/to/audio.wav")
#
# # WhisperX
# t2 = make_transcriber("whisperx", model_size="large-v2", batch_size=8, compute_type="float16")
# lines = t2.transcribe("container/path/to/audio.wav")
#
# print(lines[:3])
