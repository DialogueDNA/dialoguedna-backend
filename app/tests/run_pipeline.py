# run_pipeline.py

import logging
from audio_pipeline.pipeline import FullEmotionPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

pipeline = FullEmotionPipeline(audio_path="input_audio.wav")
pipeline.run()