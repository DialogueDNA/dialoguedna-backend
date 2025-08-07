# audio_pipeline/speaker_assigner.py

from typing import List, Dict
import torch
import torchaudio
import os

class SpeakerAssigner:
    def __init__(self, speaker_signatures: Dict[str, torch.Tensor]):
        """
        speaker_signatures: Dict of {speaker_id: embedding_tensor}
        """
        self.speaker_signatures = speaker_signatures

    def extract_embedding(self, file_path: str) -> torch.Tensor:
        # This should use the same method you used in your `VoiceSignature` class
        # Placeholder for example:
        waveform, sr = torchaudio.load(file_path)
        return self._dummy_embedding(waveform)

    def match_speakers(self, audio_paths: List[str]) -> Dict[str, str]:
        """
        Returns a mapping: {audio_path: matched_speaker_id}
        """
        result = {}

        for path in audio_paths:
            emb = self.extract_embedding(path)
            best_match = None
            best_score = -float("inf")

            for speaker_id, ref_emb in self.speaker_signatures.items():
                score = torch.nn.functional.cosine_similarity(emb, ref_emb, dim=0).item()
                if score > best_score:
                    best_score = score
                    best_match = speaker_id

            result[path] = best_match

        return result

    def _dummy_embedding(self, waveform: torch.Tensor) -> torch.Tensor:
        # Replace with real embedding logic
        return torch.mean(waveform, dim=1)
