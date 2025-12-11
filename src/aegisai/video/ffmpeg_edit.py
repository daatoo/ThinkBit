from __future__ import annotations

import subprocess
from typing import Sequence, Tuple, List, Optional
import cv2
import numpy as np

Interval = Tuple[float, float]
Box = Tuple[int, int, int, int]  # (x1, y1, x2, y2)

# ─────────────────────────────────────────────────────────
# Blur Configuration
# ─────────────────────────────────────────────────────────
DEFAULT_BLUR_KSIZE = 75       # Base kernel size
PIXELATION_FACTOR = 12        # Pixelation block size
BLUR_ITERATIONS = 3           # Number of blur passes


def blur_boxes_in_frame(
    frame: np.ndarray,
    boxes: Sequence[Box],
    ksize: int = DEFAULT_BLUR_KSIZE,
    method: str = "heavy",
) -> np.ndarray:
    """
    Apply strong blur/pixelation to bounding boxes to fully obscure content.
    
    Multiple blur methods available:
    - "heavy": Multi-pass Gaussian + median blur (best coverage)
    - "pixelate": Pixelation effect (blocky, very effective)
    - "blackout": Complete black fill (maximum obscuring)
    - "combined": Pixelation + blur (recommended)

    Args:
        frame: BGR uint8 image from OpenCV
        boxes: list of (x1, y1, x2, y2) bounding boxes
        ksize: Kernel size for blur (higher = stronger blur)
        method: Blur method to use
        
    Returns:
        Frame with blurred regions
    """
    h, w = frame.shape[:2]

    for (x1, y1, x2, y2) in boxes:
        # Clamp coordinates to frame bounds
        x1 = max(0, min(int(x1), w - 1))
        x2 = max(0, min(int(x2), w))
        y1 = max(0, min(int(y1), h - 1))
        y2 = max(0, min(int(y2), h))
        
        if x2 <= x1 or y2 <= y1:
            continue

        roi = frame[y1:y2, x1:x2]
        roi_h, roi_w = roi.shape[:2]
        
        if roi_h < 2 or roi_w < 2:
            continue
        
        # Ensure kernel size is appropriate for ROI size
        k = min(ksize, min(roi_w, roi_h) - 1)
        k = max(3, k | 1)  # Must be odd and at least 3
        
        if method == "heavy":
            # Multi-pass heavy blur for thorough obscuring
            blurred = roi.copy()
            for _ in range(BLUR_ITERATIONS):
                blurred = cv2.GaussianBlur(blurred, (k, k), 0)
            
            # Add median blur for even more smoothing
            median_k = min(k, 31)  # medianBlur has size limit
            median_k = max(3, median_k | 1)
            blurred = cv2.medianBlur(blurred, median_k)
            
            # Final Gaussian pass
            blurred = cv2.GaussianBlur(blurred, (k, k), 0)
            
        elif method == "pixelate":
            # Pixelation - very effective at obscuring details
            pixel_size = max(PIXELATION_FACTOR, min(roi_w, roi_h) // 8)
            small_w = max(1, roi_w // pixel_size)
            small_h = max(1, roi_h // pixel_size)
            
            blurred = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            blurred = cv2.resize(blurred, (roi_w, roi_h), interpolation=cv2.INTER_NEAREST)
            
        elif method == "blackout":
            # Complete black fill - maximum obscuring
            blurred = np.zeros_like(roi)
            
        elif method == "combined":
            # Pixelation + blur (recommended for best results)
            # Step 1: Pixelate
            pixel_size = max(PIXELATION_FACTOR // 2, min(roi_w, roi_h) // 10)
            small_w = max(1, roi_w // pixel_size)
            small_h = max(1, roi_h // pixel_size)
            
            blurred = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            blurred = cv2.resize(blurred, (roi_w, roi_h), interpolation=cv2.INTER_NEAREST)
            
            # Step 2: Apply Gaussian blur on top
            blur_k = max(3, (k // 2) | 1)
            blurred = cv2.GaussianBlur(blurred, (blur_k, blur_k), 0)
            
        else:
            # Default: standard multi-pass blur
            blurred = roi.copy()
            for _ in range(BLUR_ITERATIONS):
                blurred = cv2.GaussianBlur(blurred, (k, k), 0)
            blurred = cv2.medianBlur(blurred, max(3, min(k, 31) | 1))
            blurred = cv2.GaussianBlur(blurred, (k, k), 0)
        
        frame[y1:y2, x1:x2] = blurred

    return frame


def blur_full_frame(
    frame: np.ndarray,
    ksize: int = DEFAULT_BLUR_KSIZE,
) -> np.ndarray:
    """
    Apply blur to entire frame.
    """
    k = max(3, ksize | 1)
    blurred = cv2.GaussianBlur(frame, (k, k), 0)
    blurred = cv2.GaussianBlur(blurred, (k, k), 0)
    return blurred


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