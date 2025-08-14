from app.services.emotions.plugins import register_audio
from app.services.emotions.audio.hf_audio_classifier.hf_audio_classifier import HFAudioClassifier


@register_audio("hf-audio")
def build_hf_audio_classifier(model_name: str, target_sr: int = 16000) -> HFAudioClassifier:
    return HFAudioClassifier(model_name=model_name, target_sr=target_sr)