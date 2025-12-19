from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Literal, TypedDict

logger = logging.getLogger(__name__)

run_job = None
AUDIO_FILE_FILTER = None
VIDEO_FILE_AUDIO_ONLY = None
VIDEO_FILE_VIDEO_ONLY = None
VIDEO_FILE_AUDIO_VIDEO = None
PipelineConfig = None


def _ensure_pipeline_imports():
    global run_job, AUDIO_FILE_FILTER, VIDEO_FILE_AUDIO_ONLY
    global VIDEO_FILE_VIDEO_ONLY, VIDEO_FILE_AUDIO_VIDEO, PipelineConfig

    if run_job is None:
        from src.aegisai.pipeline.file_runner import run_job as _run_job
        from src.aegisai.pipeline.use_cases import (
            AUDIO_FILE_FILTER as _AUDIO_FILE_FILTER,
            VIDEO_FILE_AUDIO_ONLY as _VIDEO_FILE_AUDIO_ONLY,
            VIDEO_FILE_VIDEO_ONLY as _VIDEO_FILE_VIDEO_ONLY,
            VIDEO_FILE_AUDIO_VIDEO as _VIDEO_FILE_AUDIO_VIDEO,
        )
        from src.aegisai.pipeline.config import PipelineConfig as _PipelineConfig

        run_job = _run_job
        AUDIO_FILE_FILTER = _AUDIO_FILE_FILTER
        VIDEO_FILE_AUDIO_ONLY = _VIDEO_FILE_AUDIO_ONLY
        VIDEO_FILE_VIDEO_ONLY = _VIDEO_FILE_VIDEO_ONLY
        VIDEO_FILE_AUDIO_VIDEO = _VIDEO_FILE_AUDIO_VIDEO
        PipelineConfig = _PipelineConfig


InputType = Literal["audio", "video"]


class SegmentDict(TypedDict):
    start_ms: int
    end_ms: int
    action_type: str
    reason: str


class PipelineResult(TypedDict):
    output_path: str
    segments: List[SegmentDict]


def _select_pipeline_config(input_type: InputType, filter_audio: bool, filter_video: bool):
    if input_type == "audio":
        if not filter_audio:
            raise ValueError("Audio file must have filter_audio=True")
        return AUDIO_FILE_FILTER

    if filter_audio and filter_video:
        return VIDEO_FILE_AUDIO_VIDEO
    elif filter_audio and not filter_video:
        return VIDEO_FILE_AUDIO_ONLY
    elif filter_video and not filter_audio:
        return VIDEO_FILE_VIDEO_ONLY
    else:
        raise ValueError("At least one filter must be True")


def _convert_intervals_to_segments(intervals: List[tuple], action_type: str, reason: str) -> List[SegmentDict]:
    if not intervals:
        return []

    segments: List[SegmentDict] = []
    for interval in intervals:
        try:
            start_seconds, end_seconds = interval
            if start_seconds < 0 or end_seconds <= start_seconds:
                continue
            segments.append({
                "start_ms": int(start_seconds * 1000),
                "end_ms": int(end_seconds * 1000),
                "action_type": action_type,
                "reason": reason,
            })
        except (ValueError, TypeError):
            continue

    return segments


def process_media(
    input_path: Path,
    input_type: InputType,
    output_dir: Path,
    filter_audio: bool,
    filter_video: bool,
) -> PipelineResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"{input_path.stem}_censored{input_path.suffix}"
    output_path = output_dir / output_filename

    _ensure_pipeline_imports()

    config = _select_pipeline_config(input_type, filter_audio, filter_video)

    result = run_job(
        cfg=config,
        input_path_or_stream=str(input_path),
        output_path=str(output_path),
    )

    audio_intervals = result.get("audio_intervals") or []
    video_intervals = result.get("video_intervals") or []

    segments: List[SegmentDict] = []

    if audio_intervals:
        segments.extend(_convert_intervals_to_segments(audio_intervals, "mute", "Audio content filtered"))

    if video_intervals:
        segments.extend(_convert_intervals_to_segments(video_intervals, "blur", "Video content filtered"))

    return PipelineResult(output_path=str(output_path), segments=segments)
