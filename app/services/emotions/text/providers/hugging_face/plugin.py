from app.core.config.services.emotions import EmotionTextAnalysisConfig
from app.interfaces.services.emotions.text import EmotionTextAnalyzer
from app.services.emotions.text.providers.hugging_face.jhartmann_text_emotion_analyzer import JHartmannTextEmotionAnalyzer
from app.services.emotions.text.registry import register_emotion_text_analyzer


@register_emotion_text_analyzer("j_hartmann")
def build_jhartmann_text_emotion_analyzer(cfg: EmotionTextAnalysisConfig) -> EmotionTextAnalyzer:
    return JHartmannTextEmotionAnalyzer(cfg.j_hartmann)