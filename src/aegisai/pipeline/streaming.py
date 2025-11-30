"""
Audio-only streaming-style pipeline for offline MP4 files.

Flow:
1. Use ffmpeg to split audio from MP4 into fixed-length WAV chunks.
2. For each chunk:
   - Run speech-to-text (transcribe_audio).
   - Append to a rolling text buffer.
   - Run text moderation (analyze_text) on the full window.
3. Print moderation events when block=True.

Later we can add a video/vision worker with a similar pattern.
"""

import os
import glob
import queue
import threading
import subprocess
import tempfile
from typing import List

from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.moderation.text_rules import analyze_text, TextModerationResult


# =========================
#  Rolling text buffer
# =========================

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


# =========================
#  Workers
# =========================

def audio_worker(
    audio_q: "queue.Queue",
    event_q: "queue.Queue",
    text_buffer: TextBuffer,
) -> None:
    """
    Worker that processes audio chunks.

    audio_q items: (wav_path: str, timestamp_start: float)
    For each chunk:
      - transcribe_audio(wav_path)
      - append to TextBuffer
      - analyze_text(window_text)
      - if result.block: put event into event_q
    """
    while True:
        item = audio_q.get()
        if item is None:
            # stop signal
            print("[audio_worker] Stop signal received")
            audio_q.task_done()
            break

        wav_path, ts = item
        print(f"[audio_worker] Processing chunk at t={ts:.1f}s -> {wav_path}")

        try:
            raw = transcribe_audio(wav_path)
        except Exception as e:
            print(f"[audio_worker] Error in transcribe_audio({wav_path}): {e}")
            audio_q.task_done()
            continue

        # Normalize to a single string
        if isinstance(raw, list):
            text = " ".join(str(x) for x in raw)
        else:
            text = str(raw)

        print(f"[audio_worker] Transcript (t={ts:.1f}s): {text[:120]!r}")

        if text.strip():
            # Update rolling window
            text_buffer.add(ts, text)
            window_text = text_buffer.get_text()

            try:
                result: TextModerationResult = analyze_text(window_text)
            except Exception as e:
                print(f"[audio_worker] Error in analyze_text: {e}")
                result = TextModerationResult(
                    original_text=window_text,
                    bad_words=[],
                    count=0,
                    severity=0,
                    block=False,
                )

            print(
                f"[audio_worker] Moderation: count={result.count}, "
                f"severity={result.severity}, block={result.block}, "
                f"bad_words={result.bad_words}"
            )

            if result.block:
                # Emit a moderation event
                event_q.put({
                    "source": "audio",
                    "timestamp": ts,
                    "bad_words": result.bad_words,
                    "count": result.count,
                    "severity": result.severity,
                    "text_window": result.original_text,
                })

        audio_q.task_done()


def decision_worker(event_q: "queue.Queue") -> None:
    """
    Worker that consumes moderation events.

    To avoid spamming the same event over and over, we only print
    when (bad_words, severity) changes.
    """
    last_key = None  # <-- IMPORTANT: initialize here

    while True:
        event = event_q.get()
        if event is None:
            event_q.task_done()
            break

        # event may not always have bad_words/severity, so be safe
        bad_words = event.get("bad_words", [])
        severity = event.get("severity", 0)

        key = (tuple(sorted(bad_words)), severity)

        if key == last_key:
            # same violation as before -> ignore duplicate
            event_q.task_done()
            continue

        last_key = key

        print("=== MODERATION EVENT ===")
        print(event)
        print("========================")

        event_q.task_done()


# =========================
#  Main entry: audio-only on file
# =========================

def process_file_audio_only(
    video_path: str,
    chunk_seconds: int = 5,
    text_window_seconds: int = 30,
) -> None:
    """
    Process an MP4 file as if it were a live audio stream.

    Steps:
      - Use ffmpeg to segment the audio track into WAV chunks of length `chunk_seconds`.
      - Feed each chunk to `audio_worker` via a queue.
      - Maintain a rolling text window of `text_window_seconds`.
      - Run text moderation on that window and print events.
    """

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    audio_q: queue.Queue = queue.Queue()
    event_q: queue.Queue = queue.Queue()
    text_buffer = TextBuffer(window_seconds=text_window_seconds)

    # Start workers
    threading.Thread(
        target=audio_worker,
        args=(audio_q, event_q, text_buffer),
        daemon=True,
    ).start()

    threading.Thread(
        target=decision_worker,
        args=(event_q,),
        daemon=True,
    ).start()

    # Use a temp directory for chunks so we don't pollute the project folder
    with tempfile.TemporaryDirectory(prefix="aegis_audio_") as tmpdir:
        out_pattern = os.path.join(tmpdir, "chunk_%05d.wav")

        cmd = [
            "ffmpeg",
            "-y",                     # overwrite without asking
            "-i", video_path,         # input file
            "-vn",                    # disable video
            "-ac", "1",               # mono
            "-ar", "16000",           # 16kHz sample rate (good for STT)
            "-f", "segment",          # segment into multiple outputs
            "-segment_time", str(chunk_seconds),
            "-reset_timestamps", "1",
            out_pattern,
        ]

        print("[process_file_audio_only] Running ffmpeg segmentation...")
        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"[process_file_audio_only] ffmpeg failed: {e}")
            return

        # Find all generated chunks
        chunk_files: List[str] = sorted(
            glob.glob(os.path.join(tmpdir, "chunk_*.wav"))
        )

        print(f"[process_file_audio_only] Found {len(chunk_files)} chunks")

        # Put each chunk into the audio queue with its logical start timestamp
        for idx, wav_path in enumerate(chunk_files):
            ts = float(idx * chunk_seconds)  # e.g. 0, 5, 10, ...
            audio_q.put((wav_path, ts))

        # Signal audio worker to stop when done
        audio_q.put(None)
        audio_q.join()  # wait until audio_worker has processed all chunks

        # Signal decision worker to stop when done
        event_q.put(None)
        event_q.join()

    print("[process_file_audio_only] Done.")
