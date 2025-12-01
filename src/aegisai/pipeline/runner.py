# src/aegisai/pipeline/runner.py
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any, Optional

from src.aegisai.pipeline.config import PipelineConfig
from src.aegisai.audio.filter_file import filter_audio_file
from src.aegisai.video.filter_file import filter_video_file
from src.aegisai.audio.filter_stream import filter_audio_stream
from src.aegisai.video.filter_stream import filter_video_stream
from src.aegisai.video.mute import mute_intervals_in_video


def run_job(
    cfg: PipelineConfig,
    input_path_or_stream: Any,
    output_path: Optional[str] = None,
) -> Any:
    cfg.validate()

    if cfg.mode == "file":
        if not isinstance(input_path_or_stream, str):
            raise TypeError("For file mode, input_path_or_stream must be a file path (str).")
        if output_path is None:
            raise ValueError("For file pipelines, output_path is required.")
        return _run_file_job(cfg, input_path_or_stream, output_path)

    return _run_stream_job(cfg, input_path_or_stream)


def _extract_audio_track(video_path: str, audio_out_path: str) -> None:
    """
    Extract audio track from a video file into a standalone audio file.

    For STT it's usually convenient to:
    - force mono
    - force 16kHz sample rate
    - use a wav container

    You can tweak this later if needed.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",          # no video
        "-ac", "1",     # mono
        "-ar", "16000", # 16 kHz
        audio_out_path,
    ]
    subprocess.run(cmd, check=True)


def _run_file_job(
    cfg: PipelineConfig,
    input_path: str,
    output_path: str,
) -> Any:
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # ===== AUDIO FILE CASE =====
    if cfg.media_type == "audio":
        if not cfg.filter_audio:
            raise ValueError("Audio file pipeline without audio filtering does not make sense.")

        # Here we assume input_path is truly an audio file.
        intervals = filter_audio_file(
            audio_path=input_path,
            output_audio_path=output_path,
            chunk_seconds=5,
        )
        return {
            "audio_intervals": intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    # ===== VIDEO FILE CASE =====
    audio_intervals = None
    video_info = None

    # 3) Video file -> filtered audio, same video
    if cfg.filter_audio and not cfg.filter_video:
        with tempfile.TemporaryDirectory(prefix="aegis_video_audio_") as tmpdir:
            tmp_audio = os.path.join(tmpdir, "extracted_audio.wav")

            # 1) Extract audio track from video
            _extract_audio_track(input_path, tmp_audio)

            # 2) Run audio moderation on extracted audio (no separate audio output)
            audio_intervals = filter_audio_file(
                audio_path=tmp_audio,
                output_audio_path=None,
                chunk_seconds=5,
            )

        # 3) Apply mute intervals directly to the original video
        mute_intervals_in_video(
            video_path=input_path,
            intervals=audio_intervals,
            output_video_path=output_path,
        )

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    # 4) Video file -> filtered video, same audio
    if cfg.filter_video and not cfg.filter_audio:
        video_info = filter_video_file(input_path, output_path=output_path)
        return {
            "audio_intervals": None,
            "video_intervals": video_info.get("intervals", []),
            "output_path": output_path,
        }

    # 5) Video file -> filtered video and audio
    if cfg.filter_audio and cfg.filter_video:
        with tempfile.TemporaryDirectory(prefix="aegis_video_both_") as tmpdir:
            # Step 1: filter audio with same approach as above
            tmp_audio = os.path.join(tmpdir, "extracted_audio.wav")
            _extract_audio_track(input_path, tmp_audio)

            audio_intervals = filter_audio_file(
                audio_path=tmp_audio,
                output_audio_path=None,
                chunk_seconds=5,
            )

            # Apply audio mutes to a temp intermediate video
            tmp_video = os.path.join(tmpdir, "audio_filtered_video.mp4")
            mute_intervals_in_video(
                video_path=input_path,
                intervals=audio_intervals,
                output_video_path=tmp_video,
            )

            # Step 2: run video filter on that intermediate video
            video_info = filter_video_file(tmp_video, output_path=output_path)

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": video_info.get("intervals", []),
            "output_path": output_path,
        }

    raise ValueError("File pipeline with neither audio nor video filtering is meaningless.")


def _run_stream_job(
    cfg: PipelineConfig,
    input_stream: Any,
) -> Any:
    return True