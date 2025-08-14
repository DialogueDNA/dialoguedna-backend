from app.core.config.services.emotions import TextEmotionAnalysisConfig
from app.services.emotions.text.plugins import register_text
from app.services.emotions.text.adapters.hf_text_classifier.hf_emotion_text_analyzer import HFTextClassifier


@register_text("hf-text")
def build_hf_text_classifier(cfg: TextEmotionAnalysisConfig) -> HFTextClassifier:
    return HFTextClassifier(cfg.j_hartmann)