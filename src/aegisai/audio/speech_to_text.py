from google.cloud import speech
from pydub import AudioSegment


def transcribe_audio(file_path: str, key_path: str = "/home/david/Desktop/ThinkBit/secrets/aegis-key.json"):
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
        sample_rate_hertz=16000,
        enable_word_time_offsets=True,
    )

    response = client.recognize(config=config, audio=audio)

    # Full transcripts 
    transcripts: list[str] = []
    # Word-level info
    words: list[dict] = []

    for result in response.results:
        alternative = result.alternatives[0]
        transcripts.append(alternative.transcript)

        # Each alternative has .words if enable_word_time_offsets=True
        for w in alternative.words:
            words.append(
                {
                    "word": w.word,
                    "start": w.start_time.total_seconds(),
                    "end": w.end_time.total_seconds(),
                }
            )

    return {
        "transcripts": transcripts,
        "words": words,
    }



def convert_mp3_to_wav(input_path: str, output_path: str):
    """
    Convert MP3 → WAV (16 kHz, mono, LINEAR16)
    """
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")


