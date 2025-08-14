from app.core.config.services.emotions import AudioEmotionAnalysisConfig
from app.services.emotions.audio.hf_audio_classifier.hf_emotion_audio_analyzer import HFEmotionAudioAnalyzer
from app.services.emotions.audio.plugins import register_audio


@register_audio("hf-audio")
def build_hf_audio_classifier(cfg: AudioEmotionAnalysisConfig) -> HFEmotionAudioAnalyzer:
    return HFEmotionAudioAnalyzer(cfg.superb)