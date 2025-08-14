from __future__ import annotations

from app.ports.services.audio.enhancer import AudioEnhancer, AudioEnhancerInput, AudioEnhancerOutput


class CMGANEnhancer(AudioEnhancer):
    """
    Placeholder for CMGAN speech enhancement.
    """
    def __init__(self, cfg: CMGANConfig):
        self._cfg = cfg
        # TODO: Load the CMGAN model here
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput:
        # TODO: Implement the CMGAN enhancement logic
        raise NotImplementedError("CMGAN enhancer not wired. Install & implement before use.")
