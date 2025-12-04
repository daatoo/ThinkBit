from pydub import AudioSegment

def convert_mp3_to_wav(input_path: str, output_path: str):
    """
    Convert MP3 → WAV (16 kHz, mono, LINEAR16)
    """
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")


