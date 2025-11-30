from google.cloud import speech
from pydub import AudioSegment


def transcribe_wav(file_path: str, key_path: str = "aegis-key.json"):
    """
    Transcribe a 16kHz mono LINEAR16 WAV file using Google Speech-to-Text.
    """

    client = speech.SpeechClient.from_service_account_file(key_path)

    # Load audio file
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        language_code="en-US",
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000
    )

    response = client.recognize(config=config, audio=audio)

    transcripts = []
    for result in response.results:
        transcripts.append(result.alternatives[0].transcript)

    return transcripts


def convert_mp3_to_wav(input_path: str, output_path: str):
    """
    Convert MP3 → WAV (16 kHz, mono, LINEAR16)
    """
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")


