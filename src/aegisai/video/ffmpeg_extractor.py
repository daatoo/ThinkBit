"""
FFmpeg integration helpers for extracting frames from video sources.
"""

from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class FFmpegFrameExtractionError(RuntimeError):
    """Raised when FFmpeg fails to extract frames."""


@dataclass
class ExtractionResult:
    """Metadata describing the outcome of a frame extraction call."""

    output_paths: List[Path]
    fps: float
    duration: Optional[float] = None


class FFmpegFrameExtractor:
    """
    Encapsulates FFmpeg commands for converting videos to frame sequences.

    The extractor shells out to the system `ffmpeg` binary to avoid
    shipping large Python dependencies. Consumers should ensure FFmpeg
    is available on the host (see docs/setup.md for installation steps).
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def _ensure_ffmpeg(self) -> None:
        if shutil.which(self.ffmpeg_path) is None:
            raise FFmpegFrameExtractionError(
                "FFmpeg binary not found. Install FFmpeg and ensure it is on the PATH."
            )

    def extract_frames(
        self,
        video_path: Path | str,
        output_dir: Path | str,
        fps: float,
        overwrite: bool = True,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        image_format: str = "jpg",
    ) -> ExtractionResult:
        """
        Extract frames from `video_path` using FFmpeg's fps filter.

        Args:
            video_path: Local path to the input video file.
            output_dir: Directory that will receive the generated frames.
            fps: Target frames per second for sampling (clamped elsewhere).
            overwrite: Whether to overwrite existing frame files.
            start_time: Optional start offset (seconds) within the video.
            duration: Optional duration (seconds) to extract.
            image_format: `jpg`, `png`, etc.
        """
        self._ensure_ffmpeg()

        video_path = Path(video_path).expanduser().resolve()
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = output_dir / f"frame_%06d.{image_format}"

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
        ]

        cmd.append("-y" if overwrite else "-n")
        if start_time is not None:
            cmd.extend(["-ss", f"{start_time:.3f}"])

        cmd.extend(["-i", str(video_path)])

        if duration is not None:
            cmd.extend(["-t", f"{duration:.3f}"])

        cmd.extend(["-vf", f"fps={fps:.3f}"])
        cmd.extend(
            [
                "-qscale:v",
                "2",
                str(output_pattern),
            ]
        )

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise FFmpegFrameExtractionError(
                f"FFmpeg failed: {process.stderr.strip() or 'unknown error'}"
            )

        generated_files = sorted(output_dir.glob(f"frame_*.{image_format}"))
        return ExtractionResult(output_paths=generated_files, fps=fps, duration=duration)



