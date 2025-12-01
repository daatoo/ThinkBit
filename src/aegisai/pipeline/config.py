from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    """
    Generic configuration that describes one Aegis pipeline use case.

    - media_type: "audio" or "video"
    - mode: "file" or "stream"
    - filter_audio: whether to apply audio moderation
    - filter_video: whether to apply video/visual moderation
    """
    media_type: str          # "audio" | "video"
    mode: str                # "file" | "stream"
    filter_audio: bool
    filter_video: bool

    def validate(self) -> None:
        """
        Basic sanity checks on the config.
        You can extend this later if you add more modes/types.
        """
        if self.media_type not in {"audio", "video"}:
            raise ValueError(f"Unsupported media_type: {self.media_type}")
        if self.mode not in {"file", "stream"}:
            raise ValueError(f"Unsupported mode: {self.mode}")

        # Audio-only media cannot have filter_video
        if self.media_type == "audio" and self.filter_video:
            raise ValueError("Audio-only media cannot have filter_video=True")
