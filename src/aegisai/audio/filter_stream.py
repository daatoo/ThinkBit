from __future__ import annotations

from typing import Any


def filter_audio_stream(stream_source: Any) -> None:
    """
    Placeholder for future audio streaming moderation.

    Idea:
    - `stream_source` could be:
        - microphone input
        - RTMP/WebRTC audio stream
        - some async iterator that yields raw PCM chunks
    - You would:
        - chunk incoming audio into 5s windows
        - run transcribe + analyze + detect_toxic_segments
        - output a modified/filtered audio stream in real time
    - You can reuse:
        - the same STT + moderation logic as in filter_audio_file
        - the `audio_worker` + `TextBuffer` approach you already built.

    For now this is not implemented and will raise an error if called.
    """
    raise NotImplementedError("Audio streaming moderation is not implemented yet.")
