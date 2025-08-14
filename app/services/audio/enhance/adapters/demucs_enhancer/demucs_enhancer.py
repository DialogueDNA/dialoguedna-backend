from __future__ import annotations

from app.ports.services.audio.enhancer import AudioEnhancer, AudioEnhancerInput, AudioEnhancerOutput


class DemucsEnhancer(AudioEnhancer):
    """
    Placeholder wrapper for Demucs-based enhancement.
    Implement with demucs inference if the package is available.
    """
    def __init__(self, cfg: DemucsConfig):
        self._cfg = cfg
        # TODO: load Demucs model here (out of scope for lightweight scaffold)

    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput:
        # TODO: call demucs separation + recombination for vocal enhancement or noise removal
        raise NotImplementedError("Demucs enhancer not wired. Install & implement before use.")
