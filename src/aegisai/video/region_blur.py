from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from src.aegisai.video.ffmpeg_edit import blur_boxes_in_frame

Interval = Tuple[float, float]
Box = Tuple[int, int, int, int]


def _timestamp_in_intervals(ts: float, intervals: List[Interval]) -> bool:
    for start, end in intervals:
        if start <= ts <= end:
            return True
    return False


def _build_sample_lookup(
    object_boxes: List[Dict[str, Any]],
) -> Dict[float, List[Box]]:
    """
    object_boxes example:
      [{"timestamp": 10.0, "boxes": [(x1,y1,x2,y2), ...]}, ...]
    -> {10.0: [...], 12.0: [...], ...}
    """
    lookup: Dict[float, List[Box]] = {}
    for entry in object_boxes:
        ts = float(entry["timestamp"])
        key = round(ts, 3)
        boxes = [tuple(b) for b in entry.get("boxes", [])]
        if not boxes:
            continue
        lookup.setdefault(key, []).extend(boxes)
    return lookup


def blur_moving_objects_with_intervals(
    video_path: str | Path,
    intervals: List[Interval],
    object_boxes: List[Dict[str, Any]],
    sample_fps: float,
    output_video_path: str | Path,
    blur_ksize: int = 35,
) -> None:
    """
    Blur moving objects (their bounding boxes) only when time is inside
    unsafe intervals.

    video_path: original video with audio
    intervals: merged unsafe intervals [(start, end), ...]
    object_boxes: per-sampled-frame detection result from filter_video_file
    sample_fps: FPS used when sampling frames for Vision (e.g. 1.0)
    output_video_path: final output with blurred video + original audio
    """
    video_path = Path(video_path).expanduser().resolve()
    output_video_path = Path(output_video_path).expanduser().resolve()

    if not intervals:
        # nothing unsafe: just copy
        shutil.copy2(video_path, output_video_path)
        return

    # Map sample timestamp -> list of boxes
    sample_lookup = _build_sample_lookup(object_boxes)

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    with tempfile.TemporaryDirectory(prefix="aegis_objblur_") as tmpdir:
        tmpdir = Path(tmpdir)
        temp_video_noaudio = tmpdir / "video_blurred_noaudio.mp4"

        out = cv2.VideoWriter(
            str(temp_video_noaudio),
            fourcc,
            fps,
            (width, height),
        )

        if not out.isOpened():
            cap.release()
            raise RuntimeError("Failed to open VideoWriter")

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            ts = frame_idx / fps  # timestamp in seconds

            # Only blur if we're inside an unsafe interval
            if _timestamp_in_intervals(ts, intervals):
                # find nearest sampled timestamp to reuse its boxes
                # sample frames: 0, 1/sample_fps, 2/sample_fps, ...
                sample_index = int(round(ts * sample_fps))
                sample_ts = sample_index / sample_fps
                key = round(sample_ts, 3)
                boxes = sample_lookup.get(key, [])
                if boxes:
                    frame = blur_boxes_in_frame(frame, boxes, ksize=blur_ksize)

            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()

        # Now merge original audio with blurred video
        # 0:v comes from temp video, 1:a from original
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(temp_video_noaudio),
            "-i", str(video_path),
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:v", "copy",
            "-c:a", "copy",
            "-shortest",
            str(output_video_path),
        ]
        subprocess.run(cmd, check=True)
