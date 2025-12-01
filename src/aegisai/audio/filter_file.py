# src/aegisai/audio/filter_file.py
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import List, Tuple

from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.audio.audio_moderation import detect_toxic_segments
from src.aegisai.moderation.text_rules import analyze_text, TextModerationResult
from src.aegisai.video.segment import segment_audio_to_wav  # works for any media input
from src.aegisai.video.mute import merge_intervals


Interval = Tuple[float, float]


def _mute_intervals_in_audio_file(
    audio_path: str,
    intervals: List[Interval],
    output_audio_path: str,
) -> None:
    """
    Apply muting to an audio-only file using ffmpeg.

    If intervals is empty, the input is simply copied to output_audio_path.

    NOTE: This function assumes `audio_path` is an audio file
    (e.g. .wav, .mp3, .m4a). It does NOT handle video containers.
    """
    if not intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-c", "copy", output_audio_path],
            check=True,
        )
        return

    volume_filters = []
    for start, end in intervals:
        volume_filters.append(
            f"volume=enable='between(t,{start:.3f},{end:.3f})':volume=0"
        )

    af_filter = ",".join(volume_filters)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        audio_path,
        "-af",
        af_filter,
        "-c:a",
        "aac",  # re-encode audio; you can tune codec later
        output_audio_path,
    ]
    subprocess.run(cmd, check=True)


def filter_audio_file(
    audio_path: str,
    output_audio_path: str | None = None,
    chunk_seconds: int = 5,
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

    Returns:
        List of merged (start, end) intervals where audio should be muted.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    muted_intervals: List[Interval] = []

    with tempfile.TemporaryDirectory(prefix="aegis_audio_") as tmpdir:
        print("[filter_audio_file] Running ffmpeg segmentation...")
        try:
            # This function name says 'video_path' but it just means "ffmpeg input path".
            # It's safe to use it for audio-only files as well.
            chunk_files = segment_audio_to_wav(
                video_path=audio_path,
                output_dir=tmpdir,
                chunk_seconds=chunk_seconds,
            )
        except Exception as e:
            print(f"[filter_audio_file] Segmentation failed: {e}")
            return []

        print(f"[filter_audio_file] Found {len(chunk_files)} chunks")

        for idx, wav_path in enumerate(chunk_files):
            ts = float(idx * chunk_seconds)
            print(
                f"[filter_audio_file] Processing chunk {idx} "
                f"at t={ts:.1f}s -> {wav_path}"
            )

            try:
                raw = transcribe_audio(wav_path)
            except Exception as e:
                print(f"[filter_audio_file] Error in transcribe_audio({wav_path}): {e}")
                continue

            # Normalize STT result
            if isinstance(raw, dict):
                transcripts = raw.get("transcripts", [])
                words = raw.get("words", [])
            elif isinstance(raw, list):
                transcripts = [str(x) for x in raw]
                words = []
            else:
                transcripts = [str(raw)]
                words = []

            text = " ".join(transcripts)
            print(
                f"[filter_audio_file] Transcript (t={ts:.1f}s): {text[:120]!r}"
            )

            if text.strip():
                try:
                    result: TextModerationResult = analyze_text(text)
                except Exception as e:
                    print(f"[filter_audio_file] Error in analyze_text: {e}")
                    result = TextModerationResult(
                        original_text=text,
                        bad_words=[],
                        count=0,
                        severity=0,
                        block=False,
                    )

                print(
                    f"[filter_audio_file] Moderation: count={result.count}, "
                    f"severity={result.severity}, block={result.block}, "
                    f"bad_words={result.bad_words}"
                )

            if words:
                local_segments = detect_toxic_segments(words)
                if local_segments:
                    print(
                        f"[filter_audio_file] Toxic word segments (local): "
                        f"{local_segments}"
                    )

                for start_local, end_local in local_segments:
                    start_global = ts + start_local
                    end_global = ts + end_local
                    muted_intervals.append((start_global, end_global))

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
