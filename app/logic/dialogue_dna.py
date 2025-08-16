# app/logic/dialogue_dna.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.services.summary.prompts.prompts import PromptStyle
from app.state.app_states import AppState
from app.interfaces.services.audio import AudioType, AudioSegment
from app.interfaces.services.transcription import (
    TranscriptionSegmentInput,
    TranscriptionSegmentOutput,
)
from app.interfaces.services.emotions.audio import (
    EmotionAudioAnalyzer,
    EmotionAnalyzerByAudioOutput,
)
from app.interfaces.services.emotions.text import (
    EmotionTextAnalyzer,
    EmotionAnalyzerByTextOutput,
)
from app.interfaces.services.emotions import EmotionAnalyzerOutput
from app.interfaces.services.summary import (
    SummaryInput, SummarySegment, SummaryOutput, Summarizer
)

# --------------------------- Public dataclasses ---------------------------

@dataclass
class DialogueDNASegment:
    speaker: Optional[str]
    text: str
    start_time: Optional[float]
    end_time: Optional[float]
    emotions_text: Optional[Dict[str, float]] = None
    emotions_audio: Optional[Dict[str, float]] = None
    emotions_fused: Optional[Dict[str, float]] = None


@dataclass
class DialogueDNAResult:
    segments: List[DialogueDNASegment]
    summary_text: Optional[str] = None
    summary_bullets: Optional[List[str]] = None
    raw_summary: Optional[SummaryOutput] = None


# ----------------------------- Internal types ----------------------------

@dataclass(frozen=True)
class OverlapWindow:
    start: float
    end: float
    speakers: Tuple[str, ...]   # speakers involved in this overlap window (unique, sorted)


# ============================== Main Orchestrator ==============================

class DialogueDNALogic:
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
        if getattr(self.app.services, "transcription", None) is None or \
           getattr(self.app.services.transcription, "transcriber", None) is None:
            raise RuntimeError("Transcriber is not configured. Check ServicesConfig.transcription and plugin registration.")

    # ------------------------------- Public API -------------------------------

    def run(
        self,
        *,
        audio: AudioType,
        diarization: bool = True,
        language_hint: Optional[str] = None,
        fuse_weight_text: float = 0.5,
        fuse_weight_audio: float = 0.5,
        always_enhance_non_overlap: bool = False,
    ) -> DialogueDNAResult:
        """
        Execute the DialogueDNA pipeline on `audio`.

        `always_enhance_non_overlap`: if True and enhancer exists, also enhance non-overlap parts.
        """
        # 1) Transcribe
        segments = self._transcribe(audio=audio, diarization=diarization)

        # 2) Overlap detection + cache separation/enhancement per distinct window
        overlaps = self._detect_overlaps(segments)
        overlap_cache = self._prepare_overlap_sources(audio, overlaps)

        # 3) Emotions per segment (text + audio with overlap-aware analysis)
        result_segments: List[DialogueDNASegment] = []
        for seg in segments:
            emo_text = self._analyze_text_emotions(seg)
            emo_audio = self._analyze_audio_emotions_for_segment(
                audio=audio,
                seg=seg,
                overlaps=overlaps,
                overlap_cache=overlap_cache,
                always_enhance_non_overlap=always_enhance_non_overlap
            )
            fused = self._fuse_emotions(emo_text, emo_audio, fuse_weight_text, fuse_weight_audio)

            result_segments.append(DialogueDNASegment(
                speaker=str(seg.writer) if seg.writer is not None else None,
                text=self._normalize_text(seg.text),
                start_time=seg.start_time,
                end_time=seg.end_time,
                emotions_text=emo_text,
                emotions_audio=emo_audio,
                emotions_fused=fused,
            ))

        # 4) Optional summarization
        summary_text = None
        summary_bullets = None
        raw_summary = None
        summarizer: Optional[Summarizer] = getattr(self.app.services.summarization, "summarizer", None)
        if summarizer is not None:
            try:
                s_in = self._build_summary_input(result_segments, language_hint)
                raw_summary = summarizer.summarize(s_in)
                summary_text = getattr(raw_summary, "summary", None)
                summary_bullets = getattr(raw_summary, "bullets", None)
            except Exception:
                # keep going without summary
                raw_summary = None
                summary_text = None
                summary_bullets = None

        return DialogueDNAResult(
            segments=result_segments,
            summary_text=summary_text,
            summary_bullets=summary_bullets,
            raw_summary=raw_summary,
        )

    # ----------------------------- Pipeline steps -----------------------------

    def _transcribe(self, *, audio: AudioType, diarization: bool) -> List[TranscriptionSegmentOutput]:
        transcriber = self.app.services.transcription.transcriber
        req = TranscriptionSegmentInput(
            audio=AudioSegment(
                speaker=None,
                audio=audio,
                start_time=None,
                end_time=None,
                sample_rate=None,
                language=None,
            ),
            diarization=diarization,
        )
        out = transcriber.transcribe(req)
        # normalize
        for s in out:
            s.text = self._normalize_text(s.text or "")
        return out

    @staticmethod
    def _detect_overlaps(segments: List[TranscriptionSegmentOutput]) -> List[OverlapWindow]:
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

    def _analyze_text_emotions(self, seg: TranscriptionSegmentOutput) -> Optional[Dict[str, float]]:
        emo_text: Optional[EmotionTextAnalyzer] = getattr(self.app.services.emotion_analysis, "by_text", None)
        if emo_text is None:
            return None
        try:
            out: Optional[EmotionAnalyzerByTextOutput] = emo_text.analyze(seg)
            return dict(getattr(out, "emotions", {}) or {}) if out is not None else None
        except Exception:
            return None

    def _analyze_audio_emotions_for_segment(
        self,
        *,
        audio: AudioType,
        seg: TranscriptionSegmentOutput,
        overlaps: List[OverlapWindow],
        overlap_cache: Dict[Tuple[float, float, Tuple[str, ...]], Dict[str, AudioSegment]],
        always_enhance_non_overlap: bool
    ) -> Optional[Dict[str, float]]:
        """
        For one transcript segment:
          - Find intersecting overlap windows
          - For overlap sub-windows, analyze on separated+enhanced audio *for that speaker*
          - For non-overlap sub-windows, analyze on original (optionally enhanced) audio
          - Return duration-weighted average distribution over the full segment.
        """
        emo_audio: Optional[EmotionAudioAnalyzer] = getattr(self.app.services.emotion_analysis, "by_audio", None)
        if emo_audio is None or seg.start_time is None or seg.end_time is None:
            return None

        seg_spk = str(seg.writer) if seg.writer is not None else None
        if seg_spk is None:
            # no diarization → analyze the whole chunk on original audio
            return self._analyze_audio_distribution(
                emo_audio, AudioSegment(None, audio, seg.start_time, seg.end_time, None, None)
            )

        # Collect sub-intervals: [(start,end, audio_segment_for_analysis)]
        intervals: List[Tuple[float, float, AudioSegment]] = []
        # First, mark the whole segment as "remaining"
        remaining: List[Tuple[float, float]] = [(seg.start_time, seg.end_time)]

        # Take intersecting overlap windows
        for ow in overlaps:
            if ow.end <= seg.start_time or ow.start >= seg.end_time:
                continue  # no intersection
            if seg_spk not in ow.speakers:
                continue  # this segment's speaker not part of that overlap

            a = max(seg.start_time, ow.start)
            b = min(seg.end_time, ow.end)
            win_key = (ow.start, ow.end, ow.speakers)
            speaker_map = overlap_cache.get(win_key, {})
            # Use separated+enhanced audio for this speaker if present; otherwise fall back
            src = speaker_map.get(seg_spk)
            if src is not None:
                # narrow to [a,b] if provider doesn't handle internal trimming
                intervals.append((a, b, AudioSegment(seg_spk, src.audio, a, b, None, None)))
            # cut [a,b] out of remaining
            remaining = _subtract_interval(remaining, (a, b))

        # Non-overlap parts → original audio (optional enhance)
        enh = getattr(self.app.services.audio, "enhancer", None) \
              if getattr(self.app.services, "audio", None) and getattr(self.app.services.audio, "enhancer", None) \
              else None
        for (a, b) in remaining:
            if b <= a:
                continue
            base = AudioSegment(seg_spk, audio, a, b, None, None)
            if enh is not None and always_enhance_non_overlap:
                try:
                    base = enh.enhance(base)
                except Exception:
                    pass
            intervals.append((a, b, base))

        # Analyze each interval and weight-average by duration
        distribs: List[Tuple[float, Dict[str, float]]] = []
        for (a, b, seg_audio) in intervals:
            dur = max(0.0, (b - a))
            if dur <= 0:
                continue
            d = self._analyze_audio_distribution(emo_audio, seg_audio)
            if d:
                distribs.append((dur, d))
        return _weighted_average_distributions(distribs)

    @staticmethod
    def _analyze_audio_distribution(
        analyzer: EmotionAudioAnalyzer, audio_seg: AudioSegment
    ) -> Optional[Dict[str, float]]:
        try:
            out: Optional[EmotionAnalyzerByAudioOutput] = analyzer.analyze(audio_seg)
            return dict(getattr(out, "emotions", {}) or {}) if out is not None else None
        except Exception:
            return None

    @staticmethod
    def _build_summary_input(
        dna: List[DialogueDNASegment], language_hint: Optional[str]
    ) -> SummaryInput:
        rows: List[SummarySegment] = []
        for s in dna:
            rows.append(SummarySegment(
                text=s.text,
                speaker=s.speaker,
                emotions=EmotionAnalyzerOutput(emotions=s.emotions_fused or s.emotions_text or s.emotions_audio or {}),
            ))
        return SummaryInput(
            segments=rows,
            language=language_hint,
            per_speaker=True,
            bullets=True,
            metadata=None,
            max_tokens=None,
            style=PromptStyle.EMOTIONAL_STORY
        )

    # --------------------------- Utility helpers ---------------------------

    @staticmethod
    def _normalize_text(t: str) -> str:
        return " ".join((t or "").split())

    @staticmethod
    def _fuse_emotions(
        t: Optional[Dict[str, float]],
        a: Optional[Dict[str, float]],
        wt_text: float,
        wt_audio: float
    ) -> Optional[Dict[str, float]]:
        if t and not a:
            return dict(t)
        if a and not t:
            return dict(a)
        if not t and not a:
            return None

        def _norm(d: Dict[str, float]) -> Dict[str, float]:
            s = float(sum(max(0.0, v) for v in d.values())) or 1.0
            return {k: max(0.0, v) / s for k, v in d.items()}

        tt = _norm(t or {})
        aa = _norm(a or {})
        labels = set(tt.keys()) | set(aa.keys())
        fused = {lab: wt_text * tt.get(lab, 0.0) + wt_audio * aa.get(lab, 0.0) for lab in labels}
        total = float(sum(fused.values())) or 1.0
        return {k: v / total for k, v in fused.items()}

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
