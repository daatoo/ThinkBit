# src/aegisai/video/filter_file.py
from __future__ import annotations

import subprocess
from typing import Any, Dict, List, Tuple


def filter_video_file(
    input_path: str,
    output_path: str,
) -> Dict[str, Any]:
    """
    Placeholder for future VIDEO moderation on files.

    Current behavior:
        - Simply copies the input video to output_path (no visual filtering).
        - Returns a dict describing that no visual edits were applied.

    Future behavior (TODO):
        - Extract frames at a sampling rate (e.g., 0.5–1 FPS).
        - Call Vision API (SafeSearch / custom labels).
        - Decide which time ranges or regions are unsafe.
        - Apply blur/black-box overlays over those time ranges using ffmpeg.
        - Return structured info about what was censored.

    Args:
        input_path: Path to the input video file.
        output_path: Where to write the (in future) filtered video.

    Returns:
        A dict with at least:
            {
              "intervals": [],  # future visual intervals, empty for now
              "output_path": output_path,
            }
    """
    # Temporary behavior: just copy the video.
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c",
        "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True)

    return {
        "intervals": [],  # no visual censorship yet
        "output_path": output_path,
    }
