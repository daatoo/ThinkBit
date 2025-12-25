import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aegisai.video.live_buffer import BufferedFrame, LiveFrameBuffer


class LiveBufferTests(unittest.TestCase):
    def test_release_after_delay(self) -> None:
        buffer = LiveFrameBuffer(delay_seconds=5, max_delay_seconds=10)
        buffer.push(BufferedFrame(timestamp=0.0, payload="frame-0"))
        buffer.push(BufferedFrame(timestamp=2.0, payload="frame-1"))
        self.assertEqual(buffer.pop_ready(now=4.9), [])
        ready = buffer.pop_ready(now=5.1)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].payload, "frame-0")

    def test_max_delay_trim(self) -> None:
        buffer = LiveFrameBuffer(delay_seconds=5, max_delay_seconds=7)
        for i in range(5):
            buffer.push(BufferedFrame(timestamp=float(i), payload=f"frame-{i}"))
        # Force trim because max range exceeded
        buffer.push(BufferedFrame(timestamp=10.0, payload="frame-10"))
        self.assertLessEqual(buffer._buffer[-1].timestamp - buffer._buffer[0].timestamp, 7)


if __name__ == "__main__":
    unittest.main()


