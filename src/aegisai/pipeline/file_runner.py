from __future__ import annotations

import os
import shutil
import tempfile
import concurrent.futures
from typing import Any, Optional, List, Tuple, Dict

from src.aegisai.pipeline.config import PipelineConfig
from src.aegisai.audio.filter_file import filter_audio_file
from src.aegisai.video.filter_file import filter_video_file
from src.aegisai.video.ffmpeg_edit import mute_intervals_in_video
from src.aegisai.video.segment import extract_audio_track

Interval = Tuple[float, float]

from src.aegisai.video.region_blur import blur_moving_objects_with_intervals

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _ensure_parent_dir(path: str) -> None:
    """Create parent directory for `path` if needed."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _normalize_interval_list(result: Any) -> List[Interval]:
    """
    Normalize the output of filter_* functions into a list of (start, end) tuples.

    Accepts:
      - None                      -> []
      - list/tuple/generator      -> list(result)
      - dict with key 'intervals' -> list(dict['intervals'])

    Ensures everything is float tuples.
    """
    if result is None:
        return []

    if isinstance(result, dict):
        intervals = result.get("intervals")
    else:
        intervals = result

    if intervals is None:
        return []

    normalized: List[Interval] = []
    for iv in intervals:
        # defensive: allow e.g. (s, e) or [s, e] or numpy-like values
        s, e = iv
        normalized.append((float(s), float(e)))
    return normalized


def _copy_if_needed(src: str, dst: str) -> None:
    """
    Copy src -> dst if paths differ.

    For a "no-op" pipeline (no intervals to mute/blur) this avoids
    running a pointless ffmpeg re-encode and just copies the file.
    """
    if os.path.abspath(src) == os.path.abspath(dst):
        # Caller passed same path for in/out; nothing to do.
        return
    _ensure_parent_dir(dst)
    shutil.copy2(src, dst)


def _analyze_audio_from_video(
    video_path: str,
    tmpdir: str,
    chunk_seconds: int,
) -> List[Interval]:
    """
    Extract audio from `video_path` into `tmpdir` and run audio moderation.
    Returns a list of absolute time intervals (in seconds).
    """
    tmp_audio = os.path.join(tmpdir, "extracted_audio.wav")
    extract_audio_track(video_path, tmp_audio)

    audio_result = filter_audio_file(
        audio_path=tmp_audio,
        output_audio_path=None,        # analysis-only
        chunk_seconds=chunk_seconds,
    )
    return _normalize_interval_list(audio_result)


# -------------------------------------------------------------------
# File-based pipeline
# -------------------------------------------------------------------

def run_file_job(
    cfg: PipelineConfig,
    input_path: str,
    output_path: str,
) -> Dict[str, Any]:
    """
    Run a **file-based** moderation job (audio or video).

    Returns:
        {
            "audio_intervals": List[Interval] | None,
            "video_intervals": List[Interval] | None,
            "output_path": str,
        }
    """
    cfg.validate()

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not output_path:
        raise ValueError("output_path is required for file pipelines.")

    media_type = getattr(cfg, "media_type", None)
    if media_type not in ("audio", "video"):
        raise ValueError(f"Unsupported media_type for file pipeline: {media_type!r}")

    # Allow config to override chunk size; fallback to 5 seconds.
    audio_chunk_seconds = int(getattr(cfg, "audio_chunk_seconds", 5))

    # ---------------------------------------------------------------
    # AUDIO FILE CASE
    # ---------------------------------------------------------------
    if media_type == "audio":
        if not getattr(cfg, "filter_audio", False):
            raise ValueError("Audio file pipeline without audio filtering does not make sense.")

        _ensure_parent_dir(output_path)

        intervals = filter_audio_file(
            audio_path=input_path,
            output_audio_path=output_path,
            chunk_seconds=audio_chunk_seconds,
        )
        audio_intervals = _normalize_interval_list(intervals)

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    # ---------------------------------------------------------------
    # VIDEO FILE CASE
    # ---------------------------------------------------------------
    filter_audio_flag = bool(getattr(cfg, "filter_audio", False))
    filter_video_flag = bool(getattr(cfg, "filter_video", False))

    if not filter_audio_flag and not filter_video_flag:
        raise ValueError("File pipeline with neither audio nor video filtering is meaningless.")

    # Video file -> filtered audio, same video ----
    if filter_audio_flag and not filter_video_flag:
        with tempfile.TemporaryDirectory(prefix="aegis_video_audio_") as tmpdir:
            audio_intervals = _analyze_audio_from_video(
                video_path=input_path,
                tmpdir=tmpdir,
                chunk_seconds=audio_chunk_seconds,
            )

        if audio_intervals:
            _ensure_parent_dir(output_path)
            mute_intervals_in_video(
                video_path=input_path,
                mute_intervals=audio_intervals,
                output_video_path=output_path,
            )
        else:
            # No bad audio intervals -> just copy the original video
            _copy_if_needed(input_path, output_path)

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": None,
            "output_path": output_path,
        }

    if filter_video_flag and not filter_audio_flag:
        video_result = filter_video_file(input_path, output_path=None)
        video_intervals = _normalize_interval_list(video_result)
        print("Video intervals to blur:", video_intervals)
        if video_intervals:
            _ensure_parent_dir(output_path)
            blur_moving_objects_with_intervals(
                video_path=input_path,
                intervals=video_intervals,
                object_boxes=video_result.get("object_boxes", []),
                sample_fps=float(video_result.get("sample_fps", 8.0)),
                output_video_path=output_path,
                blur_ksize=65,           # Strong blur
                expand_boxes=True,       # Expand boxes for better coverage
                interpolate_boxes=True,  # Smooth interpolation between frames
                use_tracking=True,       # Enable object tracking
                expansion_ratio=0.25,    # 25% expansion on each side
            )
        else:
            _copy_if_needed(input_path, output_path)

        return {
            "audio_intervals": None,
            "video_intervals": video_intervals,
            "output_path": output_path,
        }

    # Video file -> filtered video and audio ----
    if filter_audio_flag and filter_video_flag:
        with tempfile.TemporaryDirectory(prefix="aegis_video_both_") as tmpdir:

            def audio_job() -> List[Interval]:
                return _analyze_audio_from_video(
                    video_path=input_path,
                    tmpdir=tmpdir,
                    chunk_seconds=audio_chunk_seconds,
                )

            def video_job() -> Dict[str, Any]:
                return filter_video_file(input_path, output_path=None)

            # Run audio + video analysis in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                audio_future = executor.submit(audio_job)
                video_future = executor.submit(video_job)

                audio_intervals = audio_future.result()
                video_result = video_future.result()
                video_intervals = _normalize_interval_list(video_result)
                object_boxes = video_result.get("object_boxes", [])
                sample_fps = float(video_result.get("sample_fps", 6.0))

            working_video = input_path

            if video_intervals:
                working_video = os.path.join(tmpdir, "video_blurred.mp4")
                blur_moving_objects_with_intervals(
                    video_path=input_path,
                    intervals=video_intervals,
                    object_boxes=object_boxes,
                    sample_fps=sample_fps,
                    output_video_path=working_video,
                    blur_ksize=65,           # Strong blur
                    expand_boxes=True,       # Expand boxes for better coverage
                    interpolate_boxes=True,  # Smooth interpolation between frames
                    use_tracking=True,       # Enable object tracking
                    expansion_ratio=0.25,    # 25% expansion on each side
                )

            if audio_intervals:
                _ensure_parent_dir(output_path)
                mute_intervals_in_video(
                    video_path=working_video,
                    mute_intervals=audio_intervals,
                    output_video_path=output_path,
                )
            else:
                _copy_if_needed(working_video, output_path)

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": video_intervals,
            "output_path": output_path,
        }

    # Should be unreachable because of earlier checks
    raise RuntimeError("Unhandled file pipeline configuration state.")


def run_job(
    cfg: PipelineConfig,
    input_path_or_stream: Any,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper that only supports **file** mode in this module.

    If you keep a separate streaming pipeline, call that from another module.
    """
    if getattr(cfg, "mode", None) != "file":
        raise ValueError("This run_job implementation only supports cfg.mode == 'file'.")

    if not isinstance(input_path_or_stream, str):
        raise TypeError("For file mode, input_path_or_stream must be a file path (str).")
    if output_path is None:
        raise ValueError("For file pipelines, output_path is required.")

    return run_file_job(cfg, input_path_or_stream, output_path)
