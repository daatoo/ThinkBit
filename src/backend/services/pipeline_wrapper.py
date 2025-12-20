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

    # Ensure GOOGLE_APPLICATION_CREDENTIALS is set
    import os
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        # Assuming project root is 3 levels up from src/backend/services?
        # layout: root/src/backend/services/pipeline_wrapper.py
        # root is 4 levels up: parent -> services, parent -> backend, parent -> src, parent -> root
        root_dir = Path(__file__).resolve().parents[3] 
        key_file = root_dir / "aegis-key.json"
        if key_file.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file)
            logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS from {key_file}")
        else:
            logger.warning(f"aegis-key.json not found at {key_file}, and GOOGLE_APPLICATION_CREDENTIALS not set.")

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
    progress_callback: callable = None,
    subtitle_path: Path | None = None,
) -> PipelineResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"{input_path.stem}_censored{input_path.suffix}"
    output_path = output_dir / output_filename

    _ensure_pipeline_imports()

    config = _select_pipeline_config(input_type, filter_audio, filter_video)

    # Inject subtitle_path into config if provided
    # Inject subtitle_path into config if provided, or attempt extraction
    extracted_subtitle_path = None
    if subtitle_path:
        import dataclasses
        config = dataclasses.replace(config, subtitle_path=str(subtitle_path))
    else:
        # Attempt to extract subtitles from the video if it's a video input
        if input_type == "video":
            from src.aegisai.video.segment import extract_subtitles_from_video
            extraction_path = output_dir / f"{input_path.stem}_extracted.srt"
            if extract_subtitles_from_video(str(input_path), str(extraction_path)):
                logger.info(f"Extracted subtitles to {extraction_path}")
                import dataclasses
                config = dataclasses.replace(config, subtitle_path=str(extraction_path))
                extracted_subtitle_path = extraction_path
            else:
                 logger.info("No subtitles extracted from video.")
    
    if config.subtitle_path:
        logger.info(f"Pipeline configured with subtitle path: {config.subtitle_path}")
        if progress_callback:
            progress_callback(1, "Pipeline configured with subtitles")

    try:
        result = run_job(
            cfg=config,
            input_path_or_stream=str(input_path),
            output_path=str(output_path),
            progress_callback=progress_callback,
        )
    finally:
        # clean up extracted subtitle file if we created one
        if extracted_subtitle_path and extracted_subtitle_path.exists():
            try:
                extracted_subtitle_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup extracted subtitle file: {e}")

    audio_intervals = result.get("audio_intervals") or []
    video_intervals = result.get("video_intervals") or []

    segments: List[SegmentDict] = []

    if audio_intervals:
        segments.extend(_convert_intervals_to_segments(audio_intervals, "mute", "Audio content filtered"))

    if video_intervals:
        segments.extend(_convert_intervals_to_segments(video_intervals, "blur", "Video content filtered"))

    return PipelineResult(output_path=str(output_path), segments=segments)
