# src/aegisai/pipeline/runner.py
from __future__ import annotations

import concurrent.futures
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from src.aegisai.audio.filter_file import filter_audio_file
from src.aegisai.audio.filter_stream import filter_audio_stream
from src.aegisai.pipeline.config import PipelineConfig
from src.aegisai.video.filter_file import (
    build_region_blur_filter,
    filter_video_file,
)
from src.aegisai.video.filter_stream import filter_video_stream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from src.aegisai.video.ffmpeg_edit import mute_intervals_in_video, blur_and_mute_intervals_in_video, blur_intervals_in_video
import concurrent.futures
from src.aegisai.video.segment import extract_audio_track
from typing import List, Tuple
=======
from src.aegisai.video.mute import mute_intervals_in_video
from src.aegisai.vision.vision_rules import RegionBox
>>>>>>> Stashed changes
=======
from src.aegisai.video.mute import mute_intervals_in_video
from src.aegisai.vision.vision_rules import RegionBox
>>>>>>> Stashed changes

def run_job(
    cfg: PipelineConfig,
    input_path_or_stream: Any,
    output_path: Optional[str] = None,
) -> Any:
    cfg.validate()

    if cfg.mode == "file":
        if not isinstance(input_path_or_stream, str):
            raise TypeError("For file mode, input_path_or_stream must be a file path (str).")
        if output_path is None:
            raise ValueError("For file pipelines, output_path is required.")
        return _run_file_job(cfg, input_path_or_stream, output_path)

    return _run_stream_job(cfg, input_path_or_stream)




def _run_file_job(
    cfg: PipelineConfig,
    input_path: str,
    output_path: str,
) -> Any:
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # ===== AUDIO FILE CASE =====
    if cfg.media_type == "audio":
        if not cfg.filter_audio:
            raise ValueError("Audio file pipeline without audio filtering does not make sense.")

        # Here we assume input_path is truly an audio file.
        intervals = filter_audio_file(
            audio_path=input_path,
            output_audio_path=output_path,
            chunk_seconds=5,
        )
        return {
            "audio_intervals": intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    # ===== VIDEO FILE CASE =====
    audio_intervals = None
    video_info = None

    # 3) Video file -> filtered audio, same video
    if cfg.filter_audio and not cfg.filter_video:
        with tempfile.TemporaryDirectory(prefix="aegis_video_audio_") as tmpdir:
            tmp_audio = os.path.join(tmpdir, "extracted_audio.wav")

            # 1) Extract audio track from video
            extract_audio_track(input_path, tmp_audio)

            # 2) Run audio moderation on extracted audio (no separate audio output)
            audio_intervals = filter_audio_file(
                audio_path=tmp_audio,
                output_audio_path=None,
                chunk_seconds=5,
            )

        # 3) Apply mute intervals directly to the original video
        mute_intervals_in_video(
            video_path=input_path,
            mute_intervals=audio_intervals,
            output_video_path=output_path,
        )

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    # 4) Video file -> filtered video, same audio
    if cfg.filter_video and not cfg.filter_audio:
        video_info = filter_video_file(input_path, output_path=output_path)
        blur_intervals_in_video(
            video_path=input_path,
            blur_intervals=video_info.get("intervals", []), 
            output_video_path=output_path
        )
        return {
            "audio_intervals": None,
            "video_intervals": video_info.get("intervals", []),
            "output_path": output_path,
        }

    # 5) Video file -> filtered video and audio
    if cfg.filter_audio and cfg.filter_video:
        with tempfile.TemporaryDirectory(prefix="aegis_video_both_") as tmpdir:

            def audio_job():
                # 1) Extract audio to temp WAV
                tmp_audio = os.path.join(tmpdir, "extracted_audio.wav")
                extract_audio_track(input_path, tmp_audio)

                # 2) Run audio moderation, return intervals
                return filter_audio_file(
                    audio_path=tmp_audio,
                    output_audio_path=None,
                    chunk_seconds=5,
                )

            def video_job():
                """
                Run video moderation, return blur intervals and targeted regions.
                Also assumes we can pass output_path=None to do analysis-only.
                """
                video_result = filter_video_file(input_path, output_path=None)
                if isinstance(video_result, dict):
                    return video_result
                if isinstance(video_result, list):
                    return {
                        "intervals": video_result,
                        "blur_regions": [
                            {
                                "start": start,
                                "end": end,
                                "box": RegionBox(
                                    label="full_frame",
                                    score=1.0,
                                    xmin=0.0,
                                    ymin=0.0,
                                    xmax=1.0,
                                    ymax=1.0,
                                ),
                            }
                            for start, end in video_result
                        ],
                    }
                return {"intervals": [], "blur_regions": []}

            # Run audio + video analysis in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                audio_future = executor.submit(audio_job)
                video_future = executor.submit(video_job)

                audio_intervals = audio_future.result()
                video_info = video_future.result() or {}
                video_intervals = video_info.get("intervals", [])
                video_blur_regions = video_info.get("blur_regions", [])

            # Single ffmpeg: blur + mute together
            blur_and_mute_intervals_in_video(
                video_path=input_path,
                blur_intervals=video_blur_regions or video_intervals,
                mute_intervals=audio_intervals,
                output_video_path=output_path,
            )

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": video_intervals,
            "video_blur_regions": video_blur_regions,
            "output_path": output_path,
        }

    raise ValueError("File pipeline with neither audio nor video filtering is meaningless.")


def _run_stream_job(
    cfg: PipelineConfig,
    input_stream: Any,
) -> Any:
    return True


def _as_region_box(box_data: Any) -> RegionBox:
    if isinstance(box_data, RegionBox):
        return box_data
    if isinstance(box_data, dict):
        return RegionBox(
            label=box_data.get("label", "full_frame"),
            score=float(box_data.get("score", 1.0)),
            xmin=float(box_data.get("xmin", 0.0)),
            ymin=float(box_data.get("ymin", 0.0)),
            xmax=float(box_data.get("xmax", 1.0)),
            ymax=float(box_data.get("ymax", 1.0)),
        )
    raise ValueError("Unsupported box data supplied for blur region.")


def _normalize_blur_regions(blur_entries) -> List[Dict[str, Any]]:
    if not blur_entries:
        return []

    normalized: List[Dict[str, Any]] = []
    for entry in blur_entries:
        if isinstance(entry, dict) and "box" in entry:
            start = float(entry.get("start", 0.0))
            end = float(entry.get("end", start))
            if end <= start:
                continue
            try:
                box = _as_region_box(entry["box"])
            except ValueError:
                continue
            normalized.append({"start": start, "end": end, "box": box})
            continue

        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            start, end = entry
            start_f = float(start)
            end_f = float(end)
            if end_f <= start_f:
                continue
            normalized.append(
                {
                    "start": start_f,
                    "end": end_f,
                    "box": RegionBox(
                        label="full_frame",
                        score=1.0,
                        xmin=0.0,
                        ymin=0.0,
                        xmax=1.0,
                        ymax=1.0,
                    ),
                }
            )

    return normalized


def blur_and_mute_intervals_in_video(
    video_path: str,
    blur_intervals,
    mute_intervals,
    output_video_path: str,
) -> None:
    """
    Apply region-aware blur (boxes produced by vision) alongside optional
    audio muting in a single ffmpeg run.

    - If both lists are empty: just copy.
    - If only blur entries exist: blur video, copy audio.
    - If only mute_intervals exist: mute audio, copy video.
    - If both exist: blur + mute together.
    """

    blur_regions = _normalize_blur_regions(blur_intervals)
    safe_mute_intervals = mute_intervals or []

    # If nothing to do, just remux
    if not blur_regions and not safe_mute_intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    cmd = ["ffmpeg", "-y", "-i", video_path]

    # ======================
    # Video filter (targeted blur)
    # ======================
    video_filter = None
    if blur_regions:
        video_filter = build_region_blur_filter(blur_regions)
        if video_filter:
            cmd += ["-vf", video_filter]
        else:
            blur_regions = []

    if not video_filter and not safe_mute_intervals:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_video_path],
            check=True,
        )
        return

    # ======================
    # Audio filter (mute)
    # ======================
    if safe_mute_intervals:
        volume_filters = []
        for start, end in safe_mute_intervals:
            volume_filters.append(
                f"volume=enable='between(t,{start:.3f},{end:.3f})':volume=0"
            )
        af_filter = ",".join(volume_filters)
        cmd += ["-af", af_filter]
    # if no mute_intervals: we won't set -af and can copy audio

    # ======================
    # Codec settings
    # ======================
    # If we used a video filter, we must re-encode video.
    if video_filter:
        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
        ]
    else:
        cmd += ["-c:v", "copy"]

    # If we used an audio filter, we must (re)encode audio.
    if safe_mute_intervals:
        cmd += ["-c:a", "aac"]
    else:
        cmd += ["-c:a", "copy"]

    cmd.append(output_video_path)

    subprocess.run(cmd, check=True)