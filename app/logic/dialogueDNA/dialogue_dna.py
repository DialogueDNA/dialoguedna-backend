from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.interfaces.logic.pipeline import Pipeline, PipelineOutput, PipelineInput
from app.interfaces.services.emotions.mixed import EmotionAnalyzerMixerInput, EmotionAnalyzerMixerOutput
from app.interfaces.services.text import TextSegment
from app.services.summary.prompts.prompts import PromptStyle
from app.state.app_states import AppState
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
    EmotionAnalyzerByTextOutput, EmotionAnalyzerByTextInput,
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

class DialogueDNALogic(Pipeline):
    """
    DialogueDNA orchestrator:
      audio -> transcription+diarization -> overlap resolution (separate+enhance) ->
      emotions (text/audio) -> fusion -> optional summary.

    Notes:
    - No "short-hands": always use `self.app` to access wired services.
    - All providers are optional except the Transcriber; logic degrades gracefully.
    """

    def __init__(self, app: AppState) -> None:
        self.app = app

    # ------------------------------- Public API -------------------------------

    def run(self, pipeline_input: PipelineInput) -> PipelineOutput:
        """
        Execute the DialogueDNA pipeline on `audio`.

        `always_enhance_non_overlap`: if True and enhancer exists, also enhance non-overlap parts.
        """

        # 1) Transcribe
        transcription_output: TranscriptionOutput = self._transcribe(audio=pipeline_input.audio)

        # Report transcription
        pipeline_input.reporter.transcription_ready(transcription_output) if pipeline_input.reporter is not None else None

        # 2) Overlap detection + cache separation/enhancement per distinct window
        overlaps = self._detect_overlaps(transcription_output)
        overlap_cache = self._prepare_overlap_sources(pipeline_input.audio, overlaps)

        # 3) Emotions per segment (text + audio with overlap-aware analysis)
        emotion_analysis_output: List[EmotionAnalyzerBundle] = []
        for segment in transcription_output:

            whom = segment.writer
            start_time = segment.start_time
            end_time = segment.end_time

            # Text emotion analysis
            analyzed_text_segment: EmotionAnalyzerByTextOutput = self._analyze_text_emotions(
                segment=segment
            )

            # Audio emotion analysis
            analyzed_audio_segment: EmotionAnalyzerByAudioOutput = self._analyze_audio_emotions_for_segment(
                audio=pipeline_input.audio,
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
        pipeline_input.reporter.emotions_ready(emotion_analysis_output) if pipeline_input.reporter is not None else None

        # 4) summarization
        summarization_output: SummaryOutput = self._summarize(
            segments=emotion_analysis_output,
            style=PromptStyle.EMOTIONAL_STORY
        )

        # Report summarization
        pipeline_input.reporter.summary_ready(summarization_output) if pipeline_input.reporter is not None else None

        return PipelineOutput(
            transcription=transcription_output,
            emotion_analysis=emotion_analysis_output,
            summarization=summarization_output
        )

    # ----------------------------- Pipeline steps -----------------------------

    def _transcribe(self, *, audio: AudioType, diarization: bool = True) -> TranscriptionOutput:
        transcriber = self.app.services.transcription.transcriber

        if transcriber is None:
            # TODO: Report
            return None

        req = TranscriptionInput(
            audio=AudioSegment(
                audio=audio
            ),
            diarization=diarization
        )

        transcript_segments = transcriber.transcribe(req)

        if transcript_segments is None:
            # TODO: Report
            return None

        # normalize
        for segment in transcript_segments:
            segment.text = self._normalize_text(segment.text or "")
        return transcript_segments

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
        sep = getattr(self.app.services.audio, "separator", None) \
              if getattr(self.app.services, "audio", None) and getattr(self.app.services.audio, "separation", None) \
              else None
        enh = getattr(self.app.services.audio, "enhancer", None) \
              if getattr(self.app.services, "audio", None) and getattr(self.app.services.audio, "enhance", None) \
              else None

        cache: Dict[Tuple[float, float, Tuple[str, ...]], Dict[str, AudioSegment]] = {}
        if not overlaps or sep is None:
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
                sources: List[AudioSegment] = sep.separate(win_seg, num_speakers=len(ow.speakers))
                # Optional enhance for each separated source
                if enh is not None:
                    enhanced: List[AudioSegment] = []
                    for s in sources:
                        try:
                            enhanced.append(enh.enhance(s))
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

    def _analyze_text_emotions(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput:
        text_analyzer: EmotionTextAnalyzer = self.app.services.emotion_analysis.by_text
        if text_analyzer is None:
            # TODO: Report
            return None
        try:
            res: EmotionAnalyzerByTextOutput = text_analyzer.analyze(segment)
            return res
        except Exception:
            # TODO: Report
            return None

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
        emotion_analyzer_by_audio: EmotionAudioAnalyzer = self.app.services.emotion_analysis.by_audio

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
        for ow in overlaps:
            if ow.end <= text_segment.start_time or ow.start >= text_segment.end_time:
                continue  # no intersection
            if segment_speaker not in ow.speakers:
                continue  # this segment's speaker not part of that overlap

            a = max(text_segment.start_time, ow.start)
            b = min(text_segment.end_time, ow.end)
            win_key = (ow.start, ow.end, ow.speakers)
            speaker_map = overlap_cache.get(win_key, {})
            # Use separated+enhanced audio for this speaker if present; otherwise fall back
            src = speaker_map.get(segment_speaker)
            if src is not None:
                # narrow to [a,b] if provider doesn't handle internal trimming
                intervals.append((a, b, AudioSegment(segment_speaker, src.audio, a, b, None, None)))
            # cut [a,b] out of remaining
            remaining = _subtract_interval(remaining, (a, b))

        # Non-overlap parts → original audio (optional enhance)
        enh = getattr(self.app.services.audio, "enhancer", None) \
              if getattr(self.app.services, "audio", None) and getattr(self.app.services.audio, "enhancer", None) \
              else None
        for (a, b) in remaining:
            if b <= a:
                continue
            base = AudioSegment(segment_speaker, audio, a, b, None, None)
            if enh is not None and always_enhance_non_overlap:
                try:
                    base = enh.enhance(base)
                except Exception:
                    pass
            intervals.append((a, b, base))

        # Analyze each interval and weight-average by duration
        distribs: List[Tuple[float, EmotionAnalyzerOutput]] = []
        for (a, b, seg_audio) in intervals:
            dur = max(0.0, (b - a))
            if dur <= 0:
                continue
            d = self._analyze_audio_distribution(emotion_analyzer_by_audio, seg_audio)
            if d:
                distribs.append((dur, d))
        return _weighted_average_distributions(distribs)

    def _fuse_emotions(self,
            emotion_analyzed_by_text: EmotionAnalyzerByTextOutput,
            emotion_analyzed_by_audio: EmotionAnalyzerByAudioOutput
        ) -> EmotionAnalyzerMixerOutput:

        mixer_analyzer = self.app.services.emotion_analysis.mixed

        if mixer_analyzer is None:
            # TODO: Report
            return None

        req: EmotionAnalyzerMixerInput = EmotionAnalyzerMixerInput(
                text_results=emotion_analyzed_by_text,
                audio_results=emotion_analyzed_by_audio
            )

        try:
            res = mixer_analyzer.fuse(req)
        except Exception:
            # TODO: Report
            return None

        return res

    @staticmethod
    def _analyze_audio_distribution(
        analyzer: EmotionAudioAnalyzer,
        audio_seg: AudioSegment
    ) -> EmotionAnalyzerByAudioOutput:
        try:
            return analyzer.analyze(audio_seg)
        except Exception:
            return None

    def _summarize(
            self, segments: List[EmotionAnalyzerBundle], style: str,
            max_tokens: int = None, language: str = None,
            per_speaker: bool = None, bullets: bool = None,
            metadata: Dict[str, str] = None) -> SummaryOutput:

        summarizer = self.app.services.summarization.summarizer

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

        summary = summarizer.summarize(req)

        if summary is None:
            # TODO: Report
            return None

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
