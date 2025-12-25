# src/aegisai/audio/text_buffer.py
from typing import List


class TextBuffer:
    """
    Stores (timestamp, text) pairs and keeps only entries from
    the last `window_seconds` seconds.
    """

    def __init__(self, window_seconds: int = 30) -> None:
        self.window_seconds = window_seconds
        self.items: List[tuple[float, str]] = []

    def add(self, timestamp: float, text: str) -> None:
        """Add a new text snippet with its start timestamp."""
        self.items.append((timestamp, text))
        self._cleanup(timestamp)

    def _cleanup(self, now: float) -> None:
        """Drop items older than `window_seconds` from the buffer."""
        self.items = [
            (t, txt) for (t, txt) in self.items
            if now - t <= self.window_seconds
        ]

    def get_text(self) -> str:
        """Return concatenated text from all items in the current window."""
        return " ".join(txt for (_, txt) in self.items)
