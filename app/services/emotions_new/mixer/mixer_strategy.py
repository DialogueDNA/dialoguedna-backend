# Path: app/services/emotions_new/mixer/mixer_strategy.py
# Purpose: Core decision logic to combine text/tone/state into final probs.
# Inputs: probs_text6, probs_tone6_mapped, state_probs6, meta{duration,is_backchannel,prev_label,prev_prob}.
# Outputs: fused_probs6 (sum=1), label, confidence, flags.
# Notes: Chooses weights by duration/backchannel, applies short-neutral rule and label stability.
