from __future__ import annotations

import subprocess
from typing import Sequence, Tuple, List
import cv2
import numpy as np
Interval = Tuple[float, float]
Box = Tuple[int, int, int, int]  # (x1, y1, x2, y2)



def blur_boxes_in_frame(
    frame: np.ndarray,
    boxes: Sequence[Box],
    ksize: int = 75,
) -> np.ndarray:
    """
    In-place Gaussian blur over the given bounding boxes.

    frame: BGR uint8 image from OpenCV
    boxes: list of (x1, y1, x2, y2)
    ksize: odd kernel size for GaussianBlur (e.g. 15, 25, 35)
    """
    h, w = frame.shape[:2]

    for (x1, y1, x2, y2) in boxes:
        # clamp to frame
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))
        if x2 <= x1 or y2 <= y1:
            continue

        roi = frame[y1:y2, x1:x2]
        # ksize must be odd
        k = max(3, ksize | 1)
        blurred = cv2.GaussianBlur(roi, (k, k), 0)
        blurred = cv2.medianBlur(blurred, k)
        blurred = cv2.GaussianBlur(blurred, (k, k), 0)
        frame[y1:y2, x1:x2] = blurred

    return frame


def blur_and_mute_intervals_in_video(
    video_path: str,
    blur_intervals: Sequence[Interval],
    mute_intervals: Sequence[Interval],
    output_video_path: str,
) -> None:
    """
    Apply center blur on `blur_intervals` and mute audio on `mute_intervals`
    in a single ffmpeg run.

    - If both lists are empty: just copy.
    - If only blur_intervals: blur video, copy audio.
    - If only mute_intervals: mute audio, copy video.
    - If both: blur + mute together.
    """

    has_video_filter = bool(blur_intervals)
    has_audio_filter = bool(mute_intervals)

    # If nothing to do, just remux
    if not has_video_filter and not has_audio_filter:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    cmd = ["ffmpeg", "-y", "-i", video_path]

    # ======================
    # Video filter (blur)
    # ======================
    if has_video_filter:
        blur_enable_exprs = [
            f"between(t,{start:.3f},{end:.3f})"
            for (start, end) in blur_intervals
        ]
        # OR over all intervals (non-zero is "true" in ffmpeg expressions)
        blur_enable_all = " + ".join(blur_enable_exprs)

        vf = (
            "[0:v]split=2[main][tmp];"
            "[tmp]crop=w=iw/2:h=ih/2:x=iw/4:y=ih/4,"
            "boxblur=luma_radius=20:luma_power=2:enable='{enable}'[blurred];"
            "[main][blurred]overlay=x=W/4:y=H/4:enable='{enable}'"
        ).format(enable=blur_enable_all)

        cmd += ["-vf", vf]

    # ======================
    # Audio filter (mute)
    # ======================
    if has_audio_filter:
        volume_filters = [
            f"volume=enable='between(t,{start:.3f},{end:.3f})':volume=0"
            for (start, end) in mute_intervals
        ]
        af_filter = ",".join(volume_filters)
        cmd += ["-af", af_filter]

    # ======================
    # Codec settings
    # ======================
    # Video: re-encode only if we used a video filter
    if has_video_filter:
        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
        ]
    else:
        cmd += ["-c:v", "copy"]

    # Audio: re-encode only if we used an audio filter
    if has_audio_filter:
        cmd += ["-c:a", "aac"]
    else:
        cmd += ["-c:a", "copy"]

    cmd.append(output_video_path)

    subprocess.run(cmd, check=True)


def mute_intervals_in_video(
    video_path: str,
    mute_intervals: List[Interval],
    output_video_path: str,
) -> None:
    """
    Apply muting to the audio track of `video_path` for all given intervals.
    If `mute_intervals` is empty, the input is simply copied to `output_video_path`.
    """
    # No muting needed: just copy/remux
    if not mute_intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    # Build volume filter string to mute all intervals
    af_filter = _build_volume_mute_filter(mute_intervals)

    cmd_mute = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-af", af_filter,
        "-c:v", "copy",   # keep video as-is
        "-c:a", "aac",    # re-encode audio because we used -af
        output_video_path,
    ]

    subprocess.run(cmd_mute, check=True)



def blur_intervals_in_video(
    video_path: str,
    blur_intervals: Sequence[Interval],
    output_video_path: str,
) -> None:
    """
    Apply center blur on `blur_intervals` in the given video.

    - Video: re-encoded with libx264 (ultrafast, zerolatency) only where enabled.
    - Audio: kept 100% untouched (stream copy, no filters).

    If `blur_intervals` is empty, the input is simply copied to `output_video_path`.
    """
    # No blur needed: just copy/remux
    if not blur_intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    cmd = ["ffmpeg", "-y", "-i", video_path]

    # Build enable expression: OR over all intervals
    blur_exprs = [
        f"between(t,{start:.3f},{end:.3f})"
        for (start, end) in blur_intervals
    ]
    enable_expr = " + ".join(blur_exprs)

    vf = (
        "[0:v]split=2[main][tmp];"
        "[tmp]crop=w=iw/2:h=ih/2:x=iw/4:y=ih/4,"
        "boxblur=luma_radius=20:luma_power=2:enable='{enable}'[blurred];"
        "[main][blurred]overlay=x=W/4:y=H/4:enable='{enable}'"
    ).format(enable=enable_expr)

    cmd += ["-vf", vf]

    # Only video re-encode
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency"]

    # Audio untouched
    cmd += ["-c:a", "copy"]

    cmd.append(output_video_path)

    subprocess.run(cmd, check=True)



def _build_volume_mute_filter(intervals: Sequence[Interval]) -> str:
    """
    Build an ffmpeg volume filter string that mutes audio
    for all given [start, end] intervals.
    """
    return ",".join(
        f"volume=enable='between(t,{start:.3f},{end:.3f})':volume=0"
        for (start, end) in intervals
    )