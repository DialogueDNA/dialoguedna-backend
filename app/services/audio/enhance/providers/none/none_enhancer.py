from __future__ import annotations

from app.interfaces.services.audio.enhancer import AudioEnhancer, AudioEnhancerInput, AudioEnhancerOutput


class NoneEnhancer(AudioEnhancer):
    """No-op enhancer; returns the input as-is."""
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput:
        return AudioEnhancerOutput(enhanced_audio=audio.audio)