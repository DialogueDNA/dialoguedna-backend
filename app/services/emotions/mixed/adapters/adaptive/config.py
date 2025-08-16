from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class MixedAdaptiveConfig:
    """
    Heuristic *adaptive* fusion of text & audio emotion_analysis.

    We compute data-driven weights per segment:
      - conf_text  = 1 - H(p_text)/log(K)     # normalized entropy (higher = more confident)
      - conf_audio = 1 - H(p_audio)/log(K)
      - agreement  = cosine(p_text, p_audio)  # similarity between the two distributions

    weights (before normalization):
      w_tilde_text  = w_text_conf * conf_text  + w_agreement * agreement
      w_tilde_audio = w_audio_conf * conf_audio + w_agreement * agreement

    Final weights are normalized so w_text + w_audio = 1 (with a small floor).

    Fusion rule:
      - "geometric":  p_fused ∝ p_text^w_text * p_audio^w_audio   (log-domain blend)
      - "linear":     p_fused =  w_text * p_text + w_audio * p_audio

    Parameters:
      w_text_conf, w_audio_conf: relative importance of each modality's confidence.
      w_agreement: importance of cross-modal agreement.
      combine: fusion rule ("geometric" is robust and scale-invariant).
      renorm: re-normalize fused scores to sum to 1.
      eps: numerical floor to avoid log/zero issues.
    """
    w_text_conf: float = 1.0
    w_audio_conf: float = 1.0
    w_agreement: float = 1.0
    combine: Literal["geometric", "linear"] = "geometric"
    renorm: bool = True
    eps: float = 1e-8
