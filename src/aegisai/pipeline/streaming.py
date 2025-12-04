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
import queue
import threading
import tempfile
from typing import List

from src.aegisai.audio.text_buffer import TextBuffer
from src.aegisai.audio.workers import audio_worker
from src.aegisai.video.segment import extract_audio_chunks_from_video
from src.aegisai.video.mute_video import merge_intervals, mute_intervals_in_video





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
    output_video_path: str | None = None,
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
    muted_intervals: list[tuple[float, float]] = []

    # Start workers
    threading.Thread(
        target=audio_worker,
        args=(audio_q, event_q, text_buffer, muted_intervals, chunk_seconds),
        daemon=True,
    ).start()

    threading.Thread(
        target=decision_worker,
        args=(event_q,),
        daemon=True,
    ).start()


    # Use a temp directory for chunks so we don't pollute the project folder
    with tempfile.TemporaryDirectory(prefix="aegis_audio_") as tmpdir:
        print("[process_file_audio_only] Running ffmpeg segmentation...")
        try:
            chunk_files = extract_audio_chunks_from_video(
                video_path=video_path,
                output_dir=tmpdir,
                chunk_seconds=chunk_seconds,
            )
        except Exception as e:
            print(f"[process_file_audio_only] segmentation failed: {e}")
            return

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


    print("[process_file_audio_only] Analysis done.")

    # If no output path was given, just stop here
    if output_video_path is None:
        print("[process_file_audio_only] No output_video_path provided, skipping mute.")
        return

    merged = merge_intervals(muted_intervals)
    print(f"[process_file_audio_only] Muted intervals: {merged}")

    print("[process_file_audio_only] Running ffmpeg mute/copy...")
    try:
        mute_intervals_in_video(
            video_path=video_path,
            intervals=merged,
            output_video_path=output_video_path,
        )
    except Exception as e:
        print(f"[process_file_audio_only] Error while muting video: {e}")
        return

    print("[process_file_audio_only] Muted video written to", output_video_path)





