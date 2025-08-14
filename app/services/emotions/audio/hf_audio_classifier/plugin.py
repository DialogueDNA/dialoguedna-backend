from app.ports.services.audio.separator import AudioSeparatorOutput
from app.ports.services.emotions.audio_analyzer import AudioSegment
from app.services.emotions.audio.hf_audio_classifier.hf_audio_classifier import HFAudioClassifier
from app.services.emotions.audio.plugins import register_audio


@register_audio("hf-audio")
def build_hf_audio_classifier(audio: AudioSegment) -> AudioSeparatorOutput:
    return HFAudioClassifier(model_name=model_name, target_sr=audio)