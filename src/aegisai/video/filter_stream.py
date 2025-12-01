# src/aegisai/video/filter_stream.py
from __future__ import annotations

from typing import Any


def filter_video_stream(stream_source: Any) -> None:
    """
    Placeholder for future VIDEO streaming moderation.

    Idea:
    - `stream_source` might be:
        - RTMP / WebRTC video stream
        - camera device index
        - async generator yielding frames
    - You would:
        - read frames in real time
        - run Vision API / safety model on sampled frames
        - decide when/where to blur
        - output a modified video stream:
            - by overlaying blur/black boxes
            - or by signaling an external video mixer/OBS plugin

    For now this is not implemented and will raise an error if called.
    """
    raise NotImplementedError("Video streaming moderation is not implemented yet.")
