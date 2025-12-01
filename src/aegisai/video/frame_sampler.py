"""
Frame sampling utilities for controlling extraction rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from src.aegisai.video.ffmpeg_extractor import FFmpegFrameExtractor


@dataclass(frozen=True)
class SamplingPlan:
    """
    Describes a sampling configuration derived from a source FPS.

    Attributes:
        source_fps: FPS reported by the source stream.
        target_fps: FPS we will sample at (1-3 fps as requested).
        stride: Number of source frames skipped between samples.
    """

    source_fps: float
    target_fps: float
    stride: int


class FrameSampler:
    """
    Provides helper methods for calculating 1–3 fps sampling plans.
    """

    def __init__(
        self,
        min_fps: float = 1.0,
        max_fps: float = 3.0,
        default_fps: float = 2.0,
    ) -> None:
        if min_fps <= 0 or max_fps <= 0:
            raise ValueError("fps bounds must be positive.")
        if min_fps > max_fps:
            raise ValueError("min_fps cannot be greater than max_fps.")
        if not (min_fps <= default_fps <= max_fps):
            raise ValueError("default_fps must be between min_fps and max_fps.")

        self.min_fps = min_fps
        self.max_fps = max_fps
        self.default_fps = default_fps

    def plan(self, source_fps: float | None) -> SamplingPlan:
        """
        Compute a sampling strategy given a source FPS, clamping to [1, 3].
        """
        if not source_fps or source_fps <= 0:
            source_fps = self.default_fps

        target_fps = min(self.max_fps, max(self.min_fps, source_fps))

        if source_fps <= target_fps:
            stride = 1
        else:
            stride = max(int(round(source_fps / target_fps)), 1)
            target_fps = source_fps / stride

        return SamplingPlan(source_fps=source_fps, target_fps=target_fps, stride=stride)

    def should_emit(self, frame_index: int, plan: SamplingPlan) -> bool:
        """
        Determine whether a frame at `frame_index` should be emitted.

        Args:
            frame_index: Zero-based index in the original frame stream.
            plan: Pre-computed sampling plan.
        """
        if frame_index < 0:
            raise ValueError("frame_index must be non-negative.")
        return frame_index % plan.stride == 0
    

FrameInfo = Tuple[str, float]  # (frame_path, timestamp_seconds)


def extract_sampled_frames_from_file(
    video_path: str | Path,
    output_dir: str | Path,
    fps: float = 1.0,
) -> List[FrameInfo]:
    """
    Use FFmpegFrameExtractor to sample frames from a video file and
    attach approximate timestamps.

    Returns:
        List of (frame_path, timestamp_seconds), where timestamp is
        index / fps (0/fps, 1/fps, 2/fps, ...).
    """
    extractor = FFmpegFrameExtractor()
    result = extractor.extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        fps=fps,
    )

    frames: List[FrameInfo] = []
    for idx, path in enumerate(result.output_paths):
        ts = idx / result.fps  # seconds
        frames.append((str(path), float(ts)))

    return frames



