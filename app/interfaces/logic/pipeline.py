from dataclasses import dataclass
from typing import Protocol, List

from app.interfaces.services.audio import AudioType
from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.summary import SummaryOutput
from app.interfaces.services.transcription import TranscriptionOutput
from app.logic.dialogueDNA.reporter import PipelineReporter


@dataclass
class PipelineInput:
    audio:      AudioType
    reporter:   PipelineReporter = None

@dataclass
class PipelineOutput:
    transcription:      TranscriptionOutput
    emotion_analysis:   List[EmotionAnalyzerBundle]
    summarization:      SummaryOutput


class Pipeline(Protocol):
    def run(self, pipeline_input: PipelineInput) -> PipelineOutput: ...