# Path: app/services/emotions_new/speaker_emotion_state/label_stability.py
# Purpose: Prevent rapid label flips (hysteresis/anti-flip).
# Inputs: prev_label, prev_prob, current_probs6, margin_threshold.
# Outputs: adjusted_probs6, flags (low_margin, kept_previous).
# Notes: Pure logic; no state-store access.
