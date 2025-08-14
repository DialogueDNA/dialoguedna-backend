from app.bootstrap.services.audio.enhance.wire_audio_enhance import wire_audio_enhance
from app.bootstrap.services.audio.separation.wire_audio_separation import wire_audio_separation


def wire_audio_utils(audio_utils, audio_utils_cfg):
    wire_audio_enhance(audio_utils.audio_enhance, audio_utils_cfg.audio_enhance)
    wire_audio_separation(audio_utils.audio_separation, audio_utils_cfg.audio_separation)