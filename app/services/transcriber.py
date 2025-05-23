"""
transcriber.py

This module defines the Transcriber service, responsible for converting audio input to text.

Responsibilities:
- Receive a path to an audio file (e.g., WAV, MP3)
- Transcribe the audio using a configurable backend:
    - Whisper (local inference)
    - or Azure Speech-to-Text (cloud-based)

Returns:
- A transcript string representing the spoken content in the audio

Note:
The actual integration (Whisper or Azure) will be implemented in later development stages.
"""

class Transcriber:
    def transcribe(self, audio_path: str) -> str:
        """
        Perform transcription on the given audio file.

        :param audio_path: Full path to the input audio file
        :return: Transcribed text as a string
        """
        # TODO: Integrate Whisper or Azure Speech-to-Text here
        return "This is a dummy transcript (backend integration pending)"
