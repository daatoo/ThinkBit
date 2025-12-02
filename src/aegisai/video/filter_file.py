from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from src.aegisai.video.frame_sampler import extract_sampled_frames_from_file
from src.aegisai.vision.safe_search import analyze_frame_moderation
from src.aegisai.vision.vision_rules import intervals_from_frames, FrameModerationResult
from src.aegisai.video.mute import merge_intervals


Interval = Tuple[float, float]


def _blur_intervals_in_video(
    video_path: str,
    intervals: List[Interval],
    output_video_path: str,
) -> None:
    """
    Apply a simple full-frame blur on all given time intervals.

    When time t is in any [start, end], the whole frame is blurred.
    Audio is left unchanged.
    """
    if not intervals:
        # No blur needed: just copy
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    # Build enable expression: OR of all intervals
    enable_exprs = [f"between(t,{s:.3f},{e:.3f})" for (s, e) in intervals]
    enable_all = " + ".join(enable_exprs)  # OR in ffmpeg expression

    #vf = f"boxblur=luma_radius=20:luma_power=2:enable='{enable_all}'"
    vf = (
        "[0:v]split=2[main][tmp];"
        "[tmp]crop=w=iw/2:h=ih/2:x=iw/4:y=ih/4,"
        "boxblur=luma_radius=20:luma_power=2:enable='{enable}'[blurred];"
        "[main][blurred]overlay=x=W/4:y=H/4:enable='{enable}'" # add [out]; if you add scale
        #"[out]scale=-1:720"
    ).format(enable=enable_all)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        vf,
        "-c:a",
        "copy",
        "-preset", "ultrafast",   # or "ultrafast"
        "-tune", "zerolatency",
        output_video_path,
    ]
    subprocess.run(cmd, check=True)


def filter_video_file(
    input_path: str,
    output_path: str,
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
      5) Blur those intervals in the video.

    Returns:
        {
          "intervals": List[(start, end)],
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
            print("[filter_video_file] No frames extracted, copying video.")
            subprocess.run(
                ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path],
                check=True,
            )
            return {"intervals": [], "output_path": output_path}

        # Decide worker count (don’t go crazy by default)
        if max_workers is None:
            # up to 8 threads, but not more than number of frames
            max_workers = min(8, len(frames))

        # 2) Full moderation per frame (IN PARALLEL)
        print(f"[filter_video_file] Analyzing frames with {max_workers} worker threads...")

        results: List[FrameModerationResult] = []

        def _moderate_one(frame_path: str, ts: float) -> FrameModerationResult:
            return analyze_frame_moderation(frame_path, timestamp=ts)

        # Submit all tasks first so they run concurrently,
        # then collect results in the SAME ORDER as frames.
        from concurrent.futures import ThreadPoolExecutor

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

        # 4) Merge intervals
        merged = merge_intervals(raw_intervals)

        print("[filter_video_file] Raw unsafe intervals:", raw_intervals)
        print("[filter_video_file] Merged unsafe intervals:", merged)

        # # 5) Apply blur
        # _blur_intervals_in_video(
        #     video_path=input_path,
        #     intervals=merged,
        #     output_video_path=output_path,
        # )

        return merged
