from dataclasses import dataclass
from typing import Protocol

from app.core.config import AppConfig
from app.interfaces.services.audio import AudioType
from app.interfaces.services.emotions import EmotionBundle
from app.interfaces.services.summary import SummaryOutput
from app.interfaces.services.transcription import TranscriptionOutput


@dataclass
class PipelineInput:
    audio: AudioType
    cfg: AppConfig

@dataclass
class PipelineOutput:
    transcription: TranscriptionOutput
    emotion_analysis: EmotionBundle
    summarization: SummaryOutput


class Pipeline(Protocol):
    _reporter = None
    def run(self, pipeline_input: PipelineInput) -> PipelineOutput: ...