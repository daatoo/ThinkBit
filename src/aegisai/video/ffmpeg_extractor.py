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
    
    Includes adaptive brightness enhancement for better AI detection in
    dark environments without overblowing bright scenes.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", enhance_brightness: bool = True):
        self.ffmpeg_path = ffmpeg_path
        self.enhance_brightness = enhance_brightness

    def _ensure_ffmpeg(self) -> None:
        if shutil.which(self.ffmpeg_path) is None:
            raise FFmpegFrameExtractionError(
                "FFmpeg binary not found. Install FFmpeg and ensure it is on the PATH."
            )

    def _build_adaptive_brightness_filter(self) -> str:
        """
        Build an FFmpeg filter for adaptive brightness enhancement.
        
        Uses a combination of:
        - curves filter with a gentle S-curve to lift shadows while preserving highlights
        - eq filter for subtle gamma correction
        
        This approach:
        - Brightens dark areas to reveal hidden details (like guns in shadows)
        - Preserves highlights to avoid overblown bright scenes
        - Maintains natural contrast
        """
        # Adaptive brightness using curves filter:
        # - Lifts shadows (dark areas) more aggressively
        # - Gentle lift in midtones  
        # - Compresses highlights to prevent overexposure
        # The curve points: input/output pairs (0=black, 1=white)
        # Format: curves=master='x0/y0 x1/y1 x2/y2 ...'
        curves_filter = (
            "curves=master='"
            "0/0 "           # Keep pure black as black
            "0.1/0.18 "      # Lift deep shadows significantly (0.1 -> 0.18)
            "0.25/0.38 "     # Lift shadows (0.25 -> 0.38) 
            "0.5/0.58 "      # Gentle midtone lift (0.5 -> 0.58)
            "0.75/0.78 "     # Minimal highlight adjustment
            "1/1"            # Keep pure white as white
            "'"
        )
        
        # Additional gamma correction for shadow recovery
        # gamma < 1 brightens shadows more than highlights
        eq_filter = "eq=gamma=1.15:saturation=1.0"
        
        return f"{curves_filter},{eq_filter}"

    def extract_frames(
        self,
        video_path: Path | str,
        output_dir: Path | str,
        fps: float,
        overwrite: bool = True,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        image_format: str = "jpg",
        enhance_brightness: Optional[bool] = None,
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
            enhance_brightness: Override instance setting for adaptive brightness.
                               Brightens dark areas for better AI detection without
                               overblowing bright scenes.
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

        # Build video filter chain
        filters = [f"fps={fps:.3f}", "scale=-1:720"]
        
        # Determine if brightness enhancement should be applied
        should_enhance = enhance_brightness if enhance_brightness is not None else self.enhance_brightness
        if should_enhance:
            filters.append(self._build_adaptive_brightness_filter())
        
        vf_filter = ",".join(filters)

        cmd.extend(["-vf", vf_filter])
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



