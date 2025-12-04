import subprocess
from typing import List, Tuple


Interval = Tuple[float, float]


def merge_intervals(intervals: List[Interval]) -> List[Interval]:
    """
    Merge overlapping or adjacent [start, end] intervals.
    """
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: x[0])
    merged: List[Interval] = []
    cur_start, cur_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= cur_end:  # overlapping or touching
            cur_end = max(cur_end, end)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end

    merged.append((cur_start, cur_end))
    return merged


def mute_intervals_in_video(
    video_path: str,
    intervals: List[Interval],
    output_video_path: str,
) -> None:
    """
    Apply muting to the audio track of `video_path` for all given intervals.
    If `intervals` is empty, the input is simply copied to `output_video_path`.
    """
    if not intervals:
        # No muting needed: just copy/remux
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    # Build volume filter string to mute all intervals
    volume_filters = []
    for start, end in intervals:
        volume_filters.append(
            f"volume=enable='between(t,{start:.3f},{end:.3f})':volume=0"
        )

    af_filter = ",".join(volume_filters)

    cmd_mute = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-af", af_filter,
        "-c:v", "copy",   # keep video as-is
        "-c:a", "aac",    # re-encode or copy as needed
        output_video_path,
    ]

    subprocess.run(cmd_mute, check=True)
