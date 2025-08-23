from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.interfaces.logic.pipeline import Pipeline, PipelineOutput, PipelineInput
from app.interfaces.services.audio.enhancer import AudioEnhancer
from app.interfaces.services.emotions.mixed import EmotionAnalyzerMixerInput, EmotionAnalyzerMixerOutput
from app.interfaces.services.text import TextSegment
from app.logic.dialogueDNA.reporter import PipelineReporter
from app.services.summary.prompts.prompts import PromptStyle
from app.state.app_states import ServicesState
from app.interfaces.services.audio import AudioType, AudioSegment
from app.interfaces.services.transcription import (
    TranscriptionInput,
    TranscriptionOutput,
)
from app.interfaces.services.emotions.audio import (
    EmotionAudioAnalyzer,
    EmotionAnalyzerByAudioOutput,
)
from app.interfaces.services.emotions.text import (
    EmotionTextAnalyzer,
    EmotionAnalyzerByTextOutput,
)
from app.interfaces.services.emotions import EmotionAnalyzerBundle, EmotionAnalyzerOutput
from app.interfaces.services.summary import (
    SummaryInput, SummaryOutput
)

# ----------------------------- Internal types ----------------------------

@dataclass(frozen=True)
class OverlapWindow:
    start: float
    end: float
    speakers: Tuple[str, ...]   # speakers involved in this overlap window (unique, sorted)

# ============================== Main Orchestrator ==============================

class DialogueDNAPipeline(Pipeline):
    """
    DialogueDNA orchestrator:
      audio -> transcription+diarization -> overlap resolution (separate+enhance) ->
      emotions (text/audio) -> fusion -> optional summary.

    Notes:
    - No "short-hands": always use `self.app` to access wired services.
    - All providers are optional except the Transcriber; logic degrades gracefully.
    """

    def __init__(self, services: ServicesState) -> None:
        self.services = services

    # ------------------------------- Public API -------------------------------

    def run(self, pipeline_input: PipelineInput) -> PipelineOutput:
        """
        Execute the DialogueDNA pipeline on `audio`.

        `always_enhance_non_overlap`: if True and enhancer exists, also enhance non-overlap parts.
        """

        transcription: TranscriptionOutput = self.transcribe(
            audio=pipeline_input.audio,
            reporter=pipeline_input.reporter
        )

        emotions: List[EmotionAnalyzerBundle] = self.analyze_emotions_on_transcript(
            audio=pipeline_input.audio,
            transcription=transcription,
            reporter=pipeline_input.reporter
        )

        summarization: SummaryOutput = self.summarize(
            segments=emotions,
            style=PromptStyle.EMOTIONAL_STORY,
            reporter = pipeline_input.reporter
        )

        return PipelineOutput(
            transcription=transcription,
            emotion_analysis=emotions,
            summarization=summarization
        )

    # ----------------------------- Pipeline steps -----------------------------

    def transcribe(self, *, audio: AudioType, diarization: bool = True, reporter: PipelineReporter = None) -> TranscriptionOutput:

        # 1) Transcribe
        transcriber = self.services.transcription.transcriber

        if transcriber is None:
            # TODO: Report
            return None

        req = TranscriptionInput(
            audio=AudioSegment(
                audio=audio
            ),
            diarization=diarization
        )

        try:
            transcription = transcriber.transcribe(req)
        except Exception:
            # TODO: Report
            return None

        # normalize
        for segment in transcription:
            segment.text = self._normalize_text(segment.text or "")

        # Report transcription
        reporter.transcription_ready(transcription) if reporter is not None else None

        return transcription

    def analyze_emotions_on_transcript(self, *, audio: AudioType, transcription: TranscriptionOutput, reporter: PipelineReporter = None) -> List[EmotionAnalyzerBundle]:

        # 2) Overlap detection + cache separation/enhancement per distinct window
        overlaps = self._detect_overlaps(transcription)
        overlap_cache = self._prepare_overlap_sources(audio, overlaps)

        # 3) Emotions per segment (text + audio with overlap-aware analysis)
        emotion_analysis_output: List[EmotionAnalyzerBundle] = []
        for segment in transcription:
            whom = segment.writer
            start_time = segment.start_time
            end_time = segment.end_time

            # Text emotion analysis
            analyzed_text_segment: EmotionAnalyzerByTextOutput = self._analyze_text_emotions(
                text_segment=segment
            )

            # Audio emotion analysis
            analyzed_audio_segment: EmotionAnalyzerByAudioOutput = self._analyze_audio_emotions_for_segment(
                audio=audio,
                text_segment=segment,
                overlaps=overlaps,
                overlap_cache=overlap_cache,
            )

            # Mixed emotion analysis
            fused: EmotionAnalyzerMixerOutput = self._fuse_emotions(
                emotion_analyzed_by_text=analyzed_text_segment,
                emotion_analyzed_by_audio=analyzed_audio_segment
            )

            # Bundle the emotion analysis results
            emotion_bundle: EmotionAnalyzerBundle = EmotionAnalyzerBundle(
                text=analyzed_text_segment,
                audio=analyzed_audio_segment,
                mixed=fused,
                whom=whom,
                start_time=start_time,
                end_time=end_time
            )

            # Save the results
            emotion_analysis_output.append(emotion_bundle)

        # Report emotion analysis
        reporter.emotions_ready(emotion_analysis_output) if reporter is not None else None

        return emotion_analysis_output

    @staticmethod
    def _detect_overlaps(segments: TranscriptionOutput) -> List[OverlapWindow]:
        """
        Sweep-line over (start,end) to find windows where >1 speakers are active.
        Assumes each segment has .start_time/.end_time and .writer (speaker label).
        """
        events: List[Tuple[float, str, int]] = []  # (time, speaker, +1 start / -1 end)
        for s in segments:
            if s.start_time is None or s.end_time is None or s.writer is None:
                continue
            events.append((float(s.start_time), str(s.writer), +1))
            events.append((float(s.end_time),   str(s.writer), -1))
        events.sort(key=lambda x: (x[0], -x[2]))  # starts before ends at same time

        active: Dict[str, int] = {}
        last_t: Optional[float] = None
        windows: List[OverlapWindow] = []
        for t, spk, delta in events:
            if last_t is not None and t > last_t:
                # between last_t and t: snapshot active speakers
                speakers_now = tuple(sorted([k for k, v in active.items() if v > 0]))
                if len(speakers_now) >= 2:
                    windows.append(OverlapWindow(start=last_t, end=t, speakers=speakers_now))
            # apply event
            active[spk] = active.get(spk, 0) + delta
            if active[spk] <= 0:
                active.pop(spk, None)
            last_t = t
        # merge adjacent windows with identical speaker sets
        merged: List[OverlapWindow] = []
        for w in windows:
            if merged and merged[-1].speakers == w.speakers and abs(merged[-1].end - w.start) < 1e-6:
                merged[-1] = OverlapWindow(start=merged[-1].start, end=w.end, speakers=w.speakers)
            else:
                merged.append(w)
        return merged

    def _prepare_overlap_sources(
        self,
        audio: AudioType,
        overlaps: List[OverlapWindow],
    ) -> Dict[Tuple[float, float, Tuple[str, ...]], Dict[str, AudioSegment]]:
        """
        For each overlap window, run separation (+ enhancement if available) once,
        and cache the per-speaker AudioSegment mapping.

        Returns:
          cache[(start, end, speakers_tuple)] = { speaker_id: AudioSegment(...), ... }
        """
        separator = getattr(self.services.audio, "separator", None) \
              if getattr(self.services, "audio", None) and getattr(self.services.audio, "separation", None) \
              else None
        enhancer = getattr(self.services.audio, "enhancer", None) \
              if getattr(self.services, "audio", None) and getattr(self.services.audio, "enhance", None) \
              else None

        cache: Dict[Tuple[float, float, Tuple[str, ...]], Dict[str, AudioSegment]] = {}
        if not overlaps or separator is None:
            return cache

        for ow in overlaps:
            win_key = (ow.start, ow.end, ow.speakers)
            win_seg = AudioSegment(
                speaker=None, audio=audio,
                start_time=ow.start, end_time=ow.end,
                sample_rate=None, language=None
            )
            try:
                # Separate N sources = number of speakers in this window
                sources: List[AudioSegment] = separator.separate(win_seg, num_speakers=len(ow.speakers))
                # Optional enhance for each separated source
                if enhancer is not None:
                    enhanced: List[AudioSegment] = []
                    for s in sources:
                        try:
                            enhanced.append(enhancer.enhance(s))
                        except Exception:
                            enhanced.append(s)
                    sources = enhanced
                # Map separated sources -> speaker IDs
                mapping = self._map_sources_to_speakers(ow, sources)
                cache[win_key] = mapping
            except Exception:
                # skip this window if separator fails
                continue

        return cache

    def _analyze_text_emotions(self, text_segment: TextSegment) -> EmotionAnalyzerByTextOutput:
        text_analyzer: EmotionTextAnalyzer = self.services.emotion_analysis.by_text

        if text_analyzer is None:
            # TODO: Report
            return None

        try:
            text_emotions: EmotionAnalyzerByTextOutput = text_analyzer.analyze(text_segment)
        except Exception:
            # TODO: Report
            return None

        return text_emotions

    def _analyze_audio_emotions_for_segment(
        self,
        *,
        audio: AudioType,
        text_segment: TextSegment,
        overlaps: List[OverlapWindow],
        overlap_cache: Dict[Tuple[float, float, Tuple[str, ...]], Dict[str, AudioSegment]],
        always_enhance_non_overlap: bool = False
    ) -> EmotionAnalyzerByAudioOutput:
        """
        For one transcript segment:
          - Find intersecting overlap windows
          - For overlap sub-windows, analyze on separated+enhanced audio *for that speaker*
          - For non-overlap sub-windows, analyze on original (optionally enhanced) audio
          - Return duration-weighted average distribution over the full segment.
        """
        emotion_analyzer_by_audio: EmotionAudioAnalyzer = self.services.emotion_analysis.by_audio

        if emotion_analyzer_by_audio is None or text_segment.start_time is None or text_segment.end_time is None:
            # TODO: Report
            return None

        segment_speaker = str(text_segment.writer) if text_segment.writer is not None else None

        if segment_speaker is None:
            # no diarization → analyze the whole chunk on original audio
            return emotion_analyzer_by_audio.analyze(
                AudioSegment(
                    audio=audio, speaker=None,
                    start_time=text_segment.start_time, end_time=text_segment.end_time,
                    language=None, sample_rate=None
                )
            )

        # Collect sub-intervals: [(start,end, audio_segment_for_analysis)]
        intervals: List[Tuple[float, float, AudioSegment]] = []
        # First, mark the whole segment as "remaining"
        remaining: List[Tuple[float, float]] = [(text_segment.start_time, text_segment.end_time)]

        # Take intersecting overlap windows
        for overlap_window in overlaps:
            if overlap_window.end <= text_segment.start_time or overlap_window.start >= text_segment.end_time:
                continue  # no intersection
            if segment_speaker not in overlap_window.speakers:
                continue  # this segment's speaker not part of that overlap

            a = max(text_segment.start_time, overlap_window.start)
            b = min(text_segment.end_time, overlap_window.end)
            win_key = (overlap_window.start, overlap_window.end, overlap_window.speakers)
            speaker_map = overlap_cache.get(win_key, {})
            # Use separated+enhanced audio for this speaker if present; otherwise fall back
            src = speaker_map.get(segment_speaker)
            if src is not None:
                # narrow to [a,b] if provider doesn't handle internal trimming
                intervals.append((a, b, AudioSegment(segment_speaker, src.audio, a, b, None, None)))
            # cut [a,b] out of remaining
            remaining = _subtract_interval(remaining, (a, b))

        # Non-overlap parts → original audio (optional enhance)
        enhancer: AudioEnhancer = self.services.audio.enhancer

        if enhancer is None:
            # TODO: Report
            return None

        for (a, b) in remaining:
            if b <= a:
                continue
            base = AudioSegment(segment_speaker, audio, a, b, None, None)
            if enhancer is not None and always_enhance_non_overlap:
                try:
                    base = enhancer.enhance(base)
                except Exception:
                    pass
            intervals.append((a, b, base))

        # Analyze each interval and weight-average by duration
        distribs: List[Tuple[float, EmotionAnalyzerOutput]] = []
        for (a, b, audio_segment) in intervals:
            dur = max(0.0, (b - a))
            if dur <= 0:
                continue
            d = emotion_analyzer_by_audio.analyze(audio_segment)
            if d:
                distribs.append((dur, d))
        return _weighted_average_distributions(distribs)

    def _fuse_emotions(self,
            emotion_analyzed_by_text: EmotionAnalyzerByTextOutput,
            emotion_analyzed_by_audio: EmotionAnalyzerByAudioOutput
        ) -> EmotionAnalyzerMixerOutput:

        mixer_analyzer = self.services.emotion_analysis.mixed

        if mixer_analyzer is None:
            # TODO: Report
            return None

        req: EmotionAnalyzerMixerInput = EmotionAnalyzerMixerInput(
                text_results=emotion_analyzed_by_text,
                audio_results=emotion_analyzed_by_audio
            )

        try:
            mixed_emotions = mixer_analyzer.fuse(req)
        except Exception:
            # TODO: Report
            return None

        return mixed_emotions

    def summarize(
            self, *, segments: List[EmotionAnalyzerBundle], style: str,
            max_tokens: int = None, language: str = None,
            per_speaker: bool = None, bullets: bool = None,
            metadata: Dict[str, str] = None, reporter: PipelineReporter = None) -> SummaryOutput:

        # 4) Summarization
        summarizer = self.services.summarization.summarizer

        if summarizer is None:
            # TODO: Report
            return None

        req = SummaryInput(
            segments=segments,
            style=style,
            max_tokens=max_tokens,
            language=language,
            per_speaker=per_speaker,
            bullets=bullets,
            metadata=metadata
        )

        try:
            summary = summarizer.summarize(req)
        except Exception:
            # TODO: Report
            return None

        # Report summarization
        reporter.summary_ready(summary) if reporter is not None else None

        return summary


    # --------------------------- Utility helpers ---------------------------

    @staticmethod
    def _normalize_text(t: str) -> str:
        return " ".join((t or "").split())

    @staticmethod
    def _map_sources_to_speakers(
        ow: OverlapWindow, sources: List[AudioSegment]
    ) -> Dict[str, AudioSegment]:
        """
        Hook for robust mapping. Current default is deterministic:
        - If count matches, assign by sorted speaker order.
        - Ifs mismatch, truncate/pad.
        You can override this by adding a 'speaker_mapper' service that uses
        embeddings or VAD statistics to decide the mapping.
        """
        speakers = list(ow.speakers)
        mapping: Dict[str, AudioSegment] = {}
        n = min(len(speakers), len(sources))
        for i in range(n):
            s_id = speakers[i]
            src = sources[i]
            mapping[s_id] = AudioSegment(
                speaker=s_id,
                audio=src.audio,
                start_time=src.start_time,
                end_time=src.end_time,
                sample_rate=src.sample_rate,
                language=src.language,
            )
        return mapping


# ----------------------------- Pure helpers -----------------------------

def _subtract_interval(intervals: List[Tuple[float, float]], cut: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Subtract [cut_start, cut_end] from a list of disjoint intervals, return the remainder."""
    c0, c1 = cut
    out: List[Tuple[float, float]] = []
    for a, b in intervals:
        if c1 <= a or c0 >= b:
            out.append((a, b))  # no overlap
        else:
            if c0 > a:
                out.append((a, min(b, c0)))
            if c1 < b:
                out.append((max(a, c1), b))
    # filter numerical noise
    return [(x, y) for (x, y) in out if y - x > 1e-6]


def _weighted_average_distributions(parts: List[Tuple[float, Dict[str, float]]]) -> Optional[Dict[str, float]]:
    if not parts:
        return None
    # normalize each part to sum to 1
    def _norm(d: Dict[str, float]) -> Dict[str, float]:
        summ = float(sum(max(0.0, v) for v in d.values())) or 1.0
        return {k: max(0.0, v) / summ for k, v in d.items()}
    labels = set().union(*[p.keys() for _, p in parts])
    total_dur = float(sum(d for d, _ in parts)) or 1.0
    acc = {lab: 0.0 for lab in labels}
    for dur, dist in parts:
        nd = _norm(dist)
        w = dur / total_dur
        for lab in labels:
            acc[lab] += w * nd.get(lab, 0.0)
    # renormalize
    s = float(sum(acc.values())) or 1.0
    return {k: v / s for k, v in acc.items()}
