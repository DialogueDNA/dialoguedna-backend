# run_pipeline.py

from dotenv import load_dotenv
import logging
from app.services.audio_pipeline.pipeline import FullEmotionPipeline
from app.core.logging import setup_logging

# Load environment variables from .env file
load_dotenv()

setup_logging()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

pipeline = FullEmotionPipeline(audio_path="services/input_audio.wav")
pipeline.run()