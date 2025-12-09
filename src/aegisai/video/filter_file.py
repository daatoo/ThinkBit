from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.aegisai.video.frame_sampler import extract_sampled_frames_from_file
from src.aegisai.vision.safe_search import analyze_frame_moderation
from src.aegisai.vision.vision_rules import intervals_from_frames, FrameModerationResult
from src.aegisai.audio.intervals import merge_intervals
from src.aegisai.vision.object_localization import localize_objects_from_path
from src.aegisai.vision.object_rules import select_problematic_objects


Interval = Tuple[float, float]

# ─────────────────────────────────────────────────────────
# Configuration for improved detection
# ─────────────────────────────────────────────────────────
DEFAULT_SAMPLE_FPS = 8.0           # Higher sampling for better temporal coverage
MIN_DETECTION_CONFIDENCE = 0.08   # Low threshold to catch more objects
MERGE_INTERVAL_GAP = 0.5          # Merge intervals within 0.5s of each other


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

    vf = (
        "[0:v]split=2[main][tmp];"
        "[tmp]crop=w=iw/2:h=ih/2:x=iw/4:y=ih/4,"
        "boxblur=luma_radius=25:luma_power=3:enable='{enable}'[blurred];"
        "[main][blurred]overlay=x=W/4:y=H/4:enable='{enable}'"
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
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        output_video_path,
    ]
    subprocess.run(cmd, check=True)


def _extend_intervals(
    intervals: List[Interval], 
    extend_before: float = 0.2, 
    extend_after: float = 0.3,
) -> List[Interval]:
    """
    Extend intervals slightly to ensure full coverage.
    
    Args:
        intervals: List of (start, end) intervals
        extend_before: Seconds to extend before each interval
        extend_after: Seconds to extend after each interval
        
    Returns:
        Extended intervals (not merged)
    """
    extended = []
    for start, end in intervals:
        new_start = max(0, start - extend_before)
        new_end = end + extend_after
        extended.append((new_start, new_end))
    return extended


def filter_video_file(
    input_path: str,
    output_path: str | None,
    sample_fps: float = DEFAULT_SAMPLE_FPS,
    max_workers: int | None = None,
    extend_intervals: bool = True,
) -> Dict[str, Any]:
    """
    VIDEO moderation on a file with improved detection accuracy.
    
    Key improvements:
    1. Higher sampling FPS (8.0) for better temporal coverage
    2. Lower confidence thresholds for object detection
    3. Interval extension to ensure full coverage
    4. Parallel processing of frame moderation and object detection

    Returns:
        {
          "intervals": List[(start, end)],
          "object_boxes": List[{"timestamp": float, "boxes": [...], "labels": [...], ...}],
          "sample_fps": float,
          "output_path": output_path,
        }
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Video not found: {input_path}")

    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as temp_dir:
        tmpdir = temp_dir

        # ─────────────────────────────────────────────────────────
        # Step 1: Sample frames from the video file
        # ─────────────────────────────────────────────────────────
        frames = extract_sampled_frames_from_file(
            video_path=input_path,
            output_dir=tmpdir,
            fps=sample_fps,
        )
        print(f"[filter_video_file] Extracted {len(frames)} frames at {sample_fps} FPS")

        if not frames:
            print("[filter_video_file] No frames extracted.")
            return {
                "intervals": [], 
                "object_boxes": [], 
                "sample_fps": sample_fps, 
                "output_path": output_path
            }

        # Decide worker count
        if max_workers is None:
            max_workers = min(24, len(frames))

        print(f"[filter_video_file] Analyzing frames with {max_workers} worker threads...")

        # ─────────────────────────────────────────────────────────
        # Step 2: Run frame moderation (SafeSearch + labels)
        # ─────────────────────────────────────────────────────────
        results: List[FrameModerationResult] = []

        def _moderate_one(frame_path: str, ts: float) -> FrameModerationResult:
            try:
                return analyze_frame_moderation(frame_path, timestamp=ts)
            except Exception as e:
                print(f"[filter_video_file] Error moderating frame at {ts:.2f}s: {e}")
                # Return a "safe" result on error
                from src.aegisai.vision.vision_rules import FrameModerationResult
                return FrameModerationResult(
                    timestamp=ts,
                    safesearch={},
                    labels={},
                    block=False,
                )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_moderate_one, frame_path, ts): (frame_path, ts)
                for (frame_path, ts) in frames
            }
            
            # Collect results in order
            frame_results_map = {}
            for fut in as_completed(futures):
                frame_path, ts = futures[fut]
                result = fut.result()
                frame_results_map[round(ts, 3)] = result
            
            # Sort by timestamp
            for (frame_path, ts) in frames:
                key = round(ts, 3)
                if key in frame_results_map:
                    results.append(frame_results_map[key])

        print(f"[filter_video_file] Got {len(results)} moderation results.")

        # Build lookup for object detection phase
        result_lookup = {round(r.timestamp, 3): r for r in results}

        # ─────────────────────────────────────────────────────────
        # Step 3: Calculate unsafe intervals from frame decisions
        # ─────────────────────────────────────────────────────────
        frame_step = 1.0 / sample_fps
        raw_intervals = intervals_from_frames(results, frame_step=frame_step)

        # Extend intervals slightly for safety margin
        if extend_intervals and raw_intervals:
            raw_intervals = _extend_intervals(raw_intervals)

        # Merge intervals
        merged = merge_intervals(raw_intervals, gap_threshold=MERGE_INTERVAL_GAP)

        print(f"[filter_video_file] Raw unsafe intervals: {len(raw_intervals)}")
        print(f"[filter_video_file] Merged unsafe intervals: {merged}")

        # ─────────────────────────────────────────────────────────
        # Step 4: Run object localization for all frames
        # ─────────────────────────────────────────────────────────
        per_frame_boxes: List[Dict[str, Any]] = []
        
        def _localize_one(frame_path: str, ts: float) -> Dict[str, Any]:
            """Localize objects in a single frame."""
            try:
                objs = localize_objects_from_path(
                    frame_path, 
                    min_confidence=MIN_DETECTION_CONFIDENCE
                )
                frame_result = result_lookup.get(round(ts, 3))
                filtered = select_problematic_objects(objs, frame_result)
                
                if filtered:
                    return {
                        "timestamp": ts,
                        "boxes": [obj.bbox for obj in filtered],
                        "labels": [obj.label for obj in filtered],
                        "reasons": [obj.reason for obj in filtered],
                        "confidences": [obj.confidence for obj in filtered],
                    }
            except Exception as e:
                print(f"[filter_video_file] Error localizing objects at {ts:.2f}s: {e}")
            
            return None

        print("[filter_video_file] Running object localization...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_localize_one, frame_path, ts): ts
                for (frame_path, ts) in frames
            }
            
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    per_frame_boxes.append(result)

        # Sort by timestamp
        per_frame_boxes.sort(key=lambda x: x["timestamp"])
        
        print(f"[filter_video_file] Found objects in {len(per_frame_boxes)} frames")
        
        # Log detection summary
        total_objects = sum(len(fb["boxes"]) for fb in per_frame_boxes)
        reasons_count: Dict[str, int] = {}
        for fb in per_frame_boxes:
            for reason in fb.get("reasons", []):
                reasons_count[reason] = reasons_count.get(reason, 0) + 1
        
        print(f"[filter_video_file] Total object detections: {total_objects}")
        print(f"[filter_video_file] Detection reasons: {reasons_count}")

        return {
            "intervals": merged,
            "object_boxes": per_frame_boxes,
            "sample_fps": sample_fps,
            "output_path": output_path,
        }

