# audio_pipeline/segment_extractor.py

import os
from base import DiarizationResult
import torchaudio

class SegmentExtractor:
    def __init__(self, audio_path: str, diarization_result: DiarizationResult):
        self.audio_path = audio_path
        self.segments = diarization_result.segments
        self.waveform, self.sr = torchaudio.load(audio_path)

    def save_chunks(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        counter = {}

        print("[SegmentExtractor] Saving speaker chunks...")
        for seg in self.segments:
            speaker = seg["speaker"]
            start_sample = int(seg["start"] * self.sr)
            end_sample = int(seg["end"] * self.sr)

            speaker_dir = os.path.join(output_dir, speaker)
            os.makedirs(speaker_dir, exist_ok=True)
            counter[speaker] = counter.get(speaker, 0) + 1

            chunk = self.waveform[:, start_sample:end_sample]
            filename = os.path.join(speaker_dir, f"chunk_{counter[speaker]:03d}.wav")
            torchaudio.save(filename, chunk, self.sr)

            print(f"[Saved] {filename}")
