from  __future__ import annotations

from src.aegisai.pipeline.config import PipelineConfig

"""
Predefined 8 high-level business use cases for Aegis.

You can import these configs from your CLI / API layer and pass them to
pipeline.runner.run_job(...)
"""

# 1) Audio file -> filtered audio file
AUDIO_FILE_FILTER = PipelineConfig(
    media_type="audio",
    mode="file",
    filter_audio=True,
    filter_video=False,
)

# 2) Audio stream -> filtered audio stream
AUDIO_STREAM_FILTER = PipelineConfig(
    media_type="audio",
    mode="stream",
    filter_audio=True,
    filter_video=False,
)

# 3) Video file -> filtered audio, same video
VIDEO_FILE_AUDIO_ONLY = PipelineConfig(
    media_type="video",
    mode="file",
    filter_audio=True,
    filter_video=False,
)

# 4) Video file -> filtered video, same audio
VIDEO_FILE_VIDEO_ONLY = PipelineConfig(
    media_type="video",
    mode="file",
    filter_audio=False,
    filter_video=True,
)

# 5) Video file -> filtered video and audio
VIDEO_FILE_AUDIO_VIDEO = PipelineConfig(
    media_type="video",
    mode="file",
    filter_audio=True,
    filter_video=True,
)

# 6) Video stream -> filtered audio, same video stream
VIDEO_STREAM_AUDIO_ONLY = PipelineConfig(
    media_type="video",
    mode="stream",
    filter_audio=True,
    filter_video=False,
)

# 7) Video stream -> filtered video, same audio stream
VIDEO_STREAM_VIDEO_ONLY = PipelineConfig(
    media_type="video",
    mode="stream",
    filter_audio=False,
    filter_video=True,
)

# 8) Video stream -> filtered video and audio stream
VIDEO_STREAM_AUDIO_VIDEO = PipelineConfig(
    media_type="video",
    mode="stream",
    filter_audio=True,
    filter_video=True,
)
