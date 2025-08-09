# audio_pipeline/pipeline.py

import os
import json
import logging

import torchaudio

from .diarizer import Diarizer
from .segment_extractor import SegmentExtractor
from .overlap_detector import OverlapDetector
from .speech_separation import SpeechSeparator
from .speaker_assigner import SpeakerAssigner
from .text_emotion_model import TextEmotionModel
from .audio_emotion_model import AudioEmotionModel
from .emotion_fusion import EmotionFusion
from .base import DiarizationResult

class FullEmotionPipeline:
    def __init__(self, audio_path: str, output_root: str = "output_sessions/session_001"):
        self.audio_path = audio_path
        self.output_root = output_root
        os.makedirs(self.output_root, exist_ok=True)

        self.text_model = TextEmotionModel()
        self.audio_model = AudioEmotionModel()
        self.fusion = EmotionFusion()
        self.speaker_signatures = {}

    def run(self):
        logging.info("🎧 Starting full emotion pipeline")

        try:
            diarizer = Diarizer(self.audio_path)
            diarized = diarizer.run()
        except Exception as e:
            logging.error(f"Failed during diarization: {e}")
            return

        try:
            extractor = SegmentExtractor(self.audio_path, diarized)
            extractor.save_chunks(self.output_root)
        except Exception as e:
            logging.error(f"Failed during segment extraction: {e}")
            return

        try:
            self.build_speaker_signatures()
        except Exception as e:
            logging.warning(f"Failed to build speaker signatures: {e}")

        try:
            self.handle_overlaps(diarized)
        except Exception as e:
            logging.warning(f"Failed during overlap handling: {e}")

        try:
            self.analyze_emotions(diarized)
        except Exception as e:
            logging.error(f"Failed during emotion analysis: {e}")
            return

        logging.info("✅ Pipeline completed successfully")

    def build_speaker_signatures(self):
        logging.info("Building voice embeddings for known speakers...")
        from audio_pipeline.speaker_assigner import SpeakerAssigner
        for speaker in os.listdir(self.output_root):
            speaker_dir = os.path.join(self.output_root, speaker)
            if not os.path.isdir(speaker_dir):
                continue
            for file in sorted(os.listdir(speaker_dir)):
                if file.endswith(".wav"):
                    path = os.path.join(speaker_dir, file)
                    assigner = SpeakerAssigner({})
                    emb = assigner.extract_embedding(path)
                    self.speaker_signatures[speaker] = emb
                    logging.info(f"✅ Embedded signature for {speaker}")
                    break

    def handle_overlaps(self, diarized: DiarizationResult):
        logging.info("🔍 Detecting overlapping speaker segments...")
        detector = OverlapDetector(diarized.segments)
        overlaps = detector.find_overlaps()

        if not overlaps:
            logging.info("✅ No overlaps found")
            return

        separator = SpeechSeparator()
        assigner = SpeakerAssigner(self.speaker_signatures)

        for i, overlap in enumerate(overlaps):
            try:
                overlap_dir = os.path.join(self.output_root, "overlaps", f"overlap_{i+1}")
                separated = separator.separate_clip(self.audio_path, overlap["start"], overlap["end"], overlap_dir)
                matches = assigner.match_speakers(separated)

                for path, speaker in matches.items():
                    speaker_dir = os.path.join(self.output_root, speaker)
                    os.makedirs(speaker_dir, exist_ok=True)
                    base = os.path.basename(path)
                    new_path = os.path.join(speaker_dir, f"overlap_{i+1}_{base}")
                    os.rename(path, new_path)
                    logging.info(f"Reassigned {base} → {speaker}")
            except Exception as e:
                logging.warning(f"⚠️ Failed to process overlap #{i+1}: {e}")

    def analyze_emotions(self, diarized: DiarizationResult):
        logging.info("📊 Running emotion analysis...")

        waveform, sr = torchaudio.load(self.audio_path)

        for seg in diarized.segments:
            try:
                speaker = seg["speaker"]
                start_sample = int(seg["start"] * sr)
                end_sample = int(seg["end"] * sr)
                text = seg["text"].strip()

                # Slice audio
                chunk = waveform[:, start_sample:end_sample]

                speaker_dir = os.path.join(self.output_root, speaker)
                chunk_name = f"{start_sample}_{end_sample}"
                chunk_path = os.path.join(speaker_dir, f"{chunk_name}.wav")

                # Save .wav file
                torchaudio.save(chunk_path, chunk, sr)

                # Run emotions
                audio_scores = self.audio_model.analyze(chunk_path)
                text_scores = self.text_model.analyze(text)
                fused_scores = self.fusion.fuse(audio_scores, text_scores)
                top_emotion = self.fusion.get_top_emotion(fused_scores)

                # Save text + emotion data
                with open(os.path.join(speaker_dir, f"{chunk_name}.txt"), "w") as f:
                    f.write(text)

                with open(os.path.join(speaker_dir, f"{chunk_name}.json"), "w") as f:
                    json.dump({
                        "text": text,
                        "start": seg["start"],
                        "end": seg["end"],
                        "audio_scores": audio_scores,
                        "text_scores": text_scores,
                        "fused_scores": fused_scores,
                        "emotion": top_emotion
                    }, f, indent=2)

                logging.info(f"[{speaker}] {chunk_name} → {top_emotion}")

            except Exception as e:
                logging.warning(f"⚠️ Failed segment {seg.get('start')}–{seg.get('end')} for {seg.get('speaker')}: {e}")

