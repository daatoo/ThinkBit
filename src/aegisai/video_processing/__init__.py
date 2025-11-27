"""
Video processing utilities for AegisAI.

Exposes FFmpeg helpers, live buffering, and frame sampling utilities
that the backend services can orchestrate.
"""

from .ffmpeg_extractor import FFmpegFrameExtractor, FFmpegFrameExtractionError
from .frame_reconstructor import (
    CensorEffectType,
    CensorInstruction,
    FrameReconstructionPipeline,
    ReconstructionError,
    ReconstructionResult,
)
from .frame_sampler import FrameSampler, SamplingPlan
from .live_buffer import BufferedFrame, LiveFrameBuffer

__all__ = [
    "FFmpegFrameExtractor",
    "FFmpegFrameExtractionError",
    "FrameSampler",
    "SamplingPlan",
    "BufferedFrame",
    "LiveFrameBuffer",
    "FrameReconstructionPipeline",
    "ReconstructionError",
    "CensorEffectType",
    "CensorInstruction",
    "ReconstructionResult",
]



