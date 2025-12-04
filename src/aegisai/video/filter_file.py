from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from src.aegisai.video.frame_sampler import extract_sampled_frames_from_file
<<<<<<< Updated upstream
from src.aegisai.vision.safe_search import analyze_frame_moderation
from src.aegisai.vision.vision_rules import intervals_from_frames, FrameModerationResult
from src.aegisai.audio.intervals import merge_intervals
=======
from src.aegisai.video.mute import merge_intervals
from src.aegisai.vision.safe_search import analyze_frame_moderation
from src.aegisai.vision.vision_rules import (
    FrameModerationResult,
    RegionBox,
    intervals_from_frames,
)
>>>>>>> Stashed changes


Interval = Tuple[float, float]


def _full_frame_box(label: str = "full_frame") -> RegionBox:
    return RegionBox(label=label, score=1.0, xmin=0.0, ymin=0.0, xmax=1.0, ymax=1.0)


def _expand_box(box: RegionBox, padding: float, min_size: float) -> RegionBox:
    xmin = max(0.0, box.xmin - padding)
    xmax = min(1.0, box.xmax + padding)
    ymin = max(0.0, box.ymin - padding)
    ymax = min(1.0, box.ymax + padding)

    if xmax <= xmin:
        xmax = min(1.0, xmin + min_size)
    if ymax <= ymin:
        ymax = min(1.0, ymin + min_size)

    width = xmax - xmin
    if width < min_size:
        delta = (min_size - width) / 2
        xmin = max(0.0, xmin - delta)
        xmax = min(1.0, xmax + delta)

    height = ymax - ymin
    if height < min_size:
        delta = (min_size - height) / 2
        ymin = max(0.0, ymin - delta)
        ymax = min(1.0, ymax + delta)

    if xmax > 1.0:
        shift = xmax - 1.0
        xmax = 1.0
        xmin = max(0.0, xmin - shift)

    if ymax > 1.0:
        shift = ymax - 1.0
        ymax = 1.0
        ymin = max(0.0, ymin - shift)

    return RegionBox(
        label=box.label,
        score=box.score,
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
    )


def build_region_blur_filter(
    blur_regions: List[Dict[str, Any]],
    padding: float = 0.05,
    min_size: float = 0.08,
) -> str | None:
    """
    Build an ffmpeg -vf graph that blurs each region only during its unsafe window.
    """
    if not blur_regions:
        return None

    parts: List[str] = []
    split_clause = f"split=outputs={len(blur_regions) + 1}[base0]"
    for idx in range(len(blur_regions)):
        split_clause += f"[r{idx}src]"
    parts.append(split_clause + ";")

    current_base = "base0"
    for idx, region in enumerate(blur_regions):
        box: RegionBox = region["box"]
        expanded = _expand_box(box, padding=padding, min_size=min_size)
        width = max(expanded.width(), min_size)
        height = max(expanded.height(), min_size)

        w_expr = f"iw*{width:.6f}"
        h_expr = f"ih*{height:.6f}"
        x_expr = f"iw*{expanded.xmin:.6f}"
        y_expr = f"ih*{expanded.ymin:.6f}"

        parts.append(
            f"[r{idx}src]"
            f"crop=w={w_expr}:h={h_expr}:x={x_expr}:y={y_expr},"
            f"boxblur=luma_radius=20:luma_power=2[blur{idx}];"
        )

        overlay_output = "" if idx == len(blur_regions) - 1 else f"[base{idx + 1}]"
        parts.append(
            f"[{current_base}][blur{idx}]"
            f"overlay=x={x_expr}:y={y_expr}:"
            f"enable='between(t,{region['start']:.3f},{region['end']:.3f})'"
            f"{overlay_output};"
        )
        current_base = f"base{idx + 1}" if overlay_output else current_base

    graph = "".join(parts)
    if graph.endswith(";"):
        graph = graph[:-1]
    return graph


def _blur_regions_in_video(
    video_path: str,
    blur_regions: List[Dict[str, Any]],
    output_video_path: str,
) -> None:
    vf = build_region_blur_filter(blur_regions)

    if not vf:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-c:a",
        "copy",
        output_video_path,
    ]
    subprocess.run(cmd, check=True)


def _frames_to_blur_regions(
    frames: List[FrameModerationResult],
    frame_step: float,
) -> List[Dict[str, Any]]:
    blur_regions: List[Dict[str, Any]] = []

    for frame in frames:
        if not frame.block:
            continue

        regions = frame.regions or [_full_frame_box()]
        for region in regions:
            blur_regions.append(
                {
                    "start": frame.timestamp,
                    "end": frame.timestamp + frame_step,
                    "box": region,
                }
            )

    return blur_regions


def filter_video_file(
    input_path: str,
    output_path: str | None,
    sample_fps: float = 1.0,
    max_workers: int | None = None,
) -> Dict[str, Any]:
    """
    VIDEO moderation on a file.

    Steps:
      1) Sample frames from file at `sample_fps` FPS (e.g. 1 frame/sec).
      2) For each frame, run analyze_frame_moderation(...) (SafeSearch + labels) in parallel threads.
      3) Convert per-frame decisions into unsafe time intervals.
      4) Merge overlapping intervals.
      5) Blur those intervals in the video (optional, when output_path is provided).

    Returns:
        {
          "intervals": List[(start, end)],
          "blur_regions": List[{"start","end","box":RegionBox}],
          "output_path": output_path,
        }
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Video not found: {input_path}")

    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as temp_dir:
        tmpdir = temp_dir

        # 1) Sample frames from the video file
        frames = extract_sampled_frames_from_file(
            video_path=input_path,
            output_dir=tmpdir,
            fps=sample_fps,
        )
        print(f"[filter_video_file] Extracted {len(frames)} frames at {sample_fps} FPS")

        if not frames:
            print("[filter_video_file] No frames extracted.")
            if output_path:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path],
                    check=True,
                )
            return {
                "intervals": [],
                "blur_regions": [],
                "output_path": output_path,
            }

        # Decide worker count (don’t go crazy by default)
        if max_workers is None:
            # up to 8 threads, but not more than number of frames
            max_workers = min(20, len(frames))

        # 2) Full moderation per frame (IN PARALLEL)
        print(f"[filter_video_file] Analyzing frames with {max_workers} worker threads...")

        results: List[FrameModerationResult] = []

        def _moderate_one(frame_path: str, ts: float) -> FrameModerationResult:
            return analyze_frame_moderation(frame_path, timestamp=ts)

        # Submit all tasks first so they run concurrently,
        # then collect results in the SAME ORDER as frames.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_moderate_one, frame_path, ts)
                for (frame_path, ts) in frames
            ]
            # This preserves order: i-th result corresponds to i-th frame
            for i, fut in enumerate(futures):
                results.append(fut.result())

        print(f"[filter_video_file] Got {len(results)} moderation results.")
        print(results)

        # 3) Frame decisions -> raw intervals
        frame_step = 1.0 / sample_fps
        raw_intervals = intervals_from_frames(results, frame_step=frame_step)
        blur_regions = _frames_to_blur_regions(results, frame_step=frame_step)

        # 4) Merge intervals
        merged = merge_intervals(raw_intervals)

        print("[filter_video_file] Raw unsafe intervals:", raw_intervals)
        print("[filter_video_file] Merged unsafe intervals:", merged)
        print(f"[filter_video_file] Built {len(blur_regions)} targeted blur regions.")

        if output_path:
            _blur_regions_in_video(
                video_path=input_path,
                blur_regions=blur_regions,
                output_video_path=output_path,
            )

        return {
            "intervals": merged,
            "blur_regions": blur_regions,
            "output_path": output_path,
        }
