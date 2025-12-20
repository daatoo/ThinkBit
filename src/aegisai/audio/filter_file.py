# src/aegisai/audio/filter_file.py
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import List, Tuple

from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.audio.intervals import detect_toxic_segments
from src.aegisai.moderation.text_rules import analyze_text, TextModerationResult
from src.aegisai.video.segment import extract_audio_chunks_from_video  # works for any media input
from src.aegisai.audio.intervals import merge_intervals
import queue
import threading

from src.aegisai.audio.text_buffer import TextBuffer
from src.aegisai.audio.workers import audio_worker
from src.aegisai.audio.subtitle_parser import parse_subtitle_file
from src.aegisai.moderation.text_rules import analyze_text
from pydub import AudioSegment

Interval = Tuple[float, float]


def _mute_intervals_in_audio_file(
    audio_path: str,
    intervals: List[Interval],
    output_audio_path: str,
) -> None:
    """
    Apply muting to an audio-only file using pydub for precise control.
    Applies fade out/in to avoid popping artifacts.

    If intervals is empty, the input is simply copied to output_audio_path.

    NOTE: This function assumes `audio_path` is an audio file
    (e.g. .wav, .mp3, .m4a).
    """

    if not intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-c", "copy", output_audio_path],
            check=True,
        )
        return

    # Load audio
    original_audio = AudioSegment.from_file(audio_path)
    total_duration_ms = len(original_audio)

    # Create silence chunk for muting (or use original_audio[s:e] - 100dB)
    # But here we just want silence.

    # Process intervals:
    # We will construct the final audio by concatenating "clean" chunks.
    # To handle overlapping or out-of-order intervals, they must be sorted and merged (which they are).

    final_audio = AudioSegment.empty()
    last_pos_ms = 0
    fade_duration_ms = 20 # 20ms fade

    for start_sec, end_sec in intervals:
        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)

        # Clamp to audio duration
        start_ms = max(0, min(start_ms, total_duration_ms))
        end_ms = max(0, min(end_ms, total_duration_ms))

        if end_ms <= start_ms:
            continue

        # Append clean audio from last_pos to start
        if start_ms > last_pos_ms:
            clean_chunk = original_audio[last_pos_ms:start_ms]
            # Fade out at the end of the clean chunk
            if len(clean_chunk) > fade_duration_ms:
                clean_chunk = clean_chunk.fade_out(fade_duration_ms)
            final_audio += clean_chunk

        # Mute period (append silence)
        mute_duration = end_ms - start_ms
        silence_chunk = AudioSegment.silent(duration=mute_duration)
        final_audio += silence_chunk

        last_pos_ms = end_ms

    # Append remaining audio
    if last_pos_ms < total_duration_ms:
        remaining = original_audio[last_pos_ms:]
        # Fade in at start of remaining
        if len(remaining) > fade_duration_ms and last_pos_ms > 0:
             remaining = remaining.fade_in(fade_duration_ms)
        final_audio += remaining

    # Export
    # Determine format from extension or default to mp3/aac
    ext = os.path.splitext(output_audio_path)[1].lower().replace(".", "")
    if not ext:
        ext = "mp3"

    # Pydub export
    final_audio.export(output_audio_path, format=ext)


def filter_audio_file(
    audio_path: str,
    output_audio_path: str | None = None,
    chunk_seconds: int = 5,
    progress_callback: Optional[callable] = None,
    subtitle_path: str | None = None,
) -> List[Interval]:
    """
    Run audio-only moderation on an AUDIO file.

    This function assumes the input is an audio file (wav/mp3/etc.), NOT a video.
    If you have a video and want to filter only its audio, do this in the pipeline:
      1) Extract audio track to a temporary audio file with ffmpeg.
      2) Call this function on that temp audio.
      3) Use the returned intervals to mute audio in the original video.

    Args:
        audio_path:
            Path to an audio file.
        output_audio_path:
            If provided, write a filtered audio file with toxic segments muted.
            If None, no audio file is written; we only return the intervals.
        chunk_seconds:
            Length of each audio chunk processed by STT.
        subtitle_path:
            Optional path to an SRT or VTT subtitle file.
            If provided, STT is skipped and subtitles are used for moderation.

    Returns:
        List of merged (start, end) intervals where audio should be muted.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    muted_intervals: List[Interval] = []

    if subtitle_path:
        print(f"[filter_audio_file] Using subtitles from: {subtitle_path}")
        if progress_callback:
            progress_callback(10, "Processing subtitles...")

        try:
            segments = parse_subtitle_file(subtitle_path)
            for seg in segments:
                text = seg["text"]
                start_ts = seg["start"]
                end_ts = seg["end"]

                result = analyze_text(text)
                if result.block:
                    print(f"[filter_audio_file] Muting subtitle segment: '{text}' ({start_ts}-{end_ts})")
                    muted_intervals.append((start_ts, end_ts))

        except Exception as e:
            print(f"[filter_audio_file] Error parsing subtitles: {e}")
            # Fallback to STT or raise? Requirement says skip STT.
            # We will return empty or partial intervals if parsing fails.
            pass

        if progress_callback:
            progress_callback(90, "Subtitle analysis complete")

    else:
        # Standard STT workflow
        text_buffer = TextBuffer()             # shared rolling text buffer
        audio_q: "queue.Queue" = queue.Queue()
        event_q: "queue.Queue" = queue.Queue()

        num_workers = 12

        # Start audio_worker threads
        workers: list[threading.Thread] = []
        for _ in range(num_workers):
            t = threading.Thread(
                target=audio_worker,
                args=(audio_q, event_q, text_buffer, muted_intervals, chunk_seconds),
                daemon=True,
            )
            t.start()
            workers.append(t)

        with tempfile.TemporaryDirectory(prefix="aegis_audio_") as tmpdir:
            print("[filter_audio_file] Running ffmpeg segmentation...")
            if progress_callback:
                progress_callback(5, "Segmenting audio...")

            try:
                # This function name says 'video_path' but it just means "ffmpeg input path".
                # It's safe to use it for audio-only files as well.
                chunk_files = extract_audio_chunks_from_video(
                    video_path=audio_path,
                    output_dir=tmpdir,
                    chunk_seconds=chunk_seconds,
                )
            except Exception as e:
                print(f"[filter_audio_file] Segmentation failed: {e}")
                for _ in range(num_workers):
                    audio_q.put(None)
                audio_q.join()
                for t in workers:
                    t.join()
                return []

            print(f"[filter_audio_file] Found {len(chunk_files)} chunks")

                    # Enqueue chunks for workers
            for idx, wav_path in enumerate(chunk_files):
                ts = float(idx * chunk_seconds)
                print(
                    f"[filter_audio_file] Queueing chunk {idx} "
                    f"at t={ts:.1f}s -> {wav_path}"
                )
                audio_q.put((wav_path, ts))

            if progress_callback:
                progress_callback(10, f"Queued {len(chunk_files)} audio chunks for analysis")

            # Send stop signals
            for _ in range(num_workers):
                audio_q.put(None)

            # Wait until all items processed
            audio_q.join()

        # Join worker threads (clean exit)
        for t in workers:
            t.join()

        if progress_callback:
            progress_callback(90, "Audio analysis complete")

    # (Optional) you can drain event_q here if you want to log/use events:
    # while not event_q.empty():
    #     evt = event_q.get()
    #     print("[filter_audio_file] Moderation event:", evt)
    #     event_q.task_done()

    merged = merge_intervals(muted_intervals)
    print(f"[filter_audio_file] Final muted intervals: {merged}")

    if output_audio_path is not None:
        print("[filter_audio_file] Writing filtered audio file...")
        try:
            _mute_intervals_in_audio_file(
                audio_path=audio_path,
                intervals=merged,
                output_audio_path=output_audio_path,
            )
            print("[filter_audio_file] Filtered audio written to", output_audio_path)
        except Exception as e:
            print(f"[filter_audio_file] Error while writing filtered audio: {e}")

    return merged