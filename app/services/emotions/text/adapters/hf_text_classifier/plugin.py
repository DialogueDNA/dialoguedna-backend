from app.services.emotions.text.plugins import register_text
from app.services.emotions.text.adapters.hf_text_classifier.hf_text_classifier import HFTextClassifier


@register_text("hf-text")
def build_hf_text_classifier(model_name: str, top_k: int | None = None) -> HFTextClassifier:
    return HFTextClassifier(model_name=model_name, top_k=top_k)