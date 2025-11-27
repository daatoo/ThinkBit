"""
Live video buffering utilities that impose a 5–10 second delay.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, List


@dataclass
class BufferedFrame:
    """
    Represents a frame stored in the buffer.

    Attributes:
        timestamp: Presentation timestamp of the frame in seconds.
        payload: Opaque frame payload (bytes, ndarray, metadata, etc.).
        metadata: Optional dictionary for additional attributes
                  (e.g., camera id, ffmpeg sequence number).
    """

    timestamp: float
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class LiveFrameBuffer:
    """
    Maintains a rolling buffer that outputs frames after a fixed delay.

    The buffer enforces:
        * `delay_seconds` – minimum latency before frames are released
        * `max_delay_seconds` – upper bound to avoid runaway latency
    """

    def __init__(self, delay_seconds: float = 5.0, max_delay_seconds: float = 10.0):
        if delay_seconds < 5 or delay_seconds > 10:
            raise ValueError("delay_seconds must remain between 5 and 10 seconds.")
        if max_delay_seconds < delay_seconds:
            raise ValueError("max_delay_seconds cannot be less than delay_seconds.")

        self.delay_seconds = delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self._buffer: Deque[BufferedFrame] = deque()

    def push(self, frame: BufferedFrame) -> None:
        """Insert a new frame into the buffer."""
        if frame.timestamp < 0:
            raise ValueError("Frame timestamp must be non-negative.")
        self._buffer.append(frame)
        self._trim_buffer()

    def pop_ready(self, now: float) -> List[BufferedFrame]:
        """
        Return frames that have satisfied the minimum delay.

        Args:
            now: Current stream time in seconds.
        """
        ready: List[BufferedFrame] = []
        while self._buffer and now - self._buffer[0].timestamp >= self.delay_seconds:
            ready.append(self._buffer.popleft())
        self._trim_buffer()
        return ready

    def _trim_buffer(self) -> None:
        """
        Ensure we never exceed the configured max delay window.
        """
        while self._buffer and (
            self._buffer[-1].timestamp - self._buffer[0].timestamp
        ) > self.max_delay_seconds:
            self._buffer.popleft()

    def __len__(self) -> int:
        return len(self._buffer)



