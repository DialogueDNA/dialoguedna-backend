from typing import Optional

from app.services.audio.separation.adapters.sepformer_separator.sepformer_separator import SepformerSeparator
from app.services.emotions.plugins import register_separator


@register_separator("sepformer")
def build_sepformer_separator(model_hub: str = "speechbrain/sepformer-whamr", device: Optional[str] = None) -> SepformerSeparator:
    return SepformerSeparator(model_hub=model_hub, device=device)