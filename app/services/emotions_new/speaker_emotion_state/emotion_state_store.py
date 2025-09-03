# Path: app/services/emotions_new/speaker_emotion_state/emotion_state_store.py
# Purpose: Rolling per-speaker emotional state management.
# Provides: get_state/update_state, decay (γ), last_label/last_prob, 3-label median smoothing.
# Inputs: speaker_id, current_probs6, timestamp/utter_idx (optional).
# Outputs: updated state_probs6, last_label, flags (state_carried, transition_neutral).
