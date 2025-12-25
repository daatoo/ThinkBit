from google.cloud import speech
from src.aegisai.moderation.bad_words_list import BAD_WORDS


_CLIENT: speech.SpeechClient | None = None

def _get_client() -> speech.SpeechClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = speech.SpeechClient()
    return _CLIENT

def transcribe_audio(file_path: str):
    """
    Transcribe a 16kHz mono LINEAR16 WAV file using Google Speech-to-Text.
    """

    client = _get_client()

    # Load audio file
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    # Boost recognition of bad words to improve detection in songs
    speech_context = speech.SpeechContext(
        phrases=list(BAD_WORDS),
        boost=20.0
    )

    config = speech.RecognitionConfig(
        language_code="en-US",
        model="video",
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        enable_word_time_offsets=True,
        speech_contexts=[speech_context],
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



