from app.bootstrap.services.emotions.audio.wire_audio_analysis import wire_audio_analysis
from app.bootstrap.services.emotions.mixed.wire_mixed_analysis import wire_mixed_analysis
from app.bootstrap.services.emotions.text.wire_text_analysis import wire_text_analysis
from app.core.config.services import EmotionAnalysisConfig
from app.state.app_states import EmotionAnalysisState


def wire_emotion_analysis(emotion_analysis: EmotionAnalysisState, emotion_analysis_cfg: EmotionAnalysisConfig) -> None:
    wire_text_analysis(emotion_analysis.by_text, emotion_analysis_cfg.by_text)
    wire_audio_analysis(emotion_analysis.by_audio, emotion_analysis_cfg.by_audio)
    wire_mixed_analysis(emotion_analysis.mixed, emotion_analysis_cfg.mixed)