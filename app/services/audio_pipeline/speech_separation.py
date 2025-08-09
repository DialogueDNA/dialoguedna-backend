# audio_pipeline/speech_separation.py

import os
from typing import List
import torchaudio
from speechbrain.inference.separation import SepformerSeparation as Separator  # updated import

class SpeechSeparator:
    def __init__(self, model_dir: str = "pretrained_models/sepformer"):
        self.separator = Separator.from_hparams(
            source="speechbrain/sepformer-wsj02mix",
            savedir=model_dir
        )

    def separate_clip(self, audio_path: str, start: float, end: float, out_dir: str) -> List[str]:
        os.makedirs(out_dir, exist_ok=True)

        # Load full audio
        waveform, sr = torchaudio.load(audio_path)

        # Convert times to sample indices
        start_sample = int(start * sr)
        end_sample = int(end * sr)

        # Slice waveform
        segment = waveform[:, start_sample:end_sample]
        temp_path = os.path.join(out_dir, "temp_overlap.wav")
        torchaudio.save(temp_path, segment, sr)

        # Separate with SepFormer
        est_sources = self.separator.separate_file(path=temp_path)

        output_files = []
        for i, source in enumerate(est_sources):
            output_path = os.path.join(out_dir, f"separated_speaker_{i+1}.wav")
            torchaudio.save(output_path, source.cpu(), 8000)
            output_files.append(output_path)

        os.remove(temp_path)
        return output_files
