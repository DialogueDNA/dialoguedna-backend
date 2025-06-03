import os
from pydub import AudioSegment

class AudioConverter:
    @staticmethod
    def convert_to_wav(input_path: str, output_path: str) -> None:
        """
        Converts an audio file to WAV format.

        :param input_path: Path to the input audio file
        :param output_path: Path to save the converted .wav file
        """
        # Load audio from input path
        audio = AudioSegment.from_file(input_path)

        # Export as WAV
        audio.export(output_path, format="wav")
