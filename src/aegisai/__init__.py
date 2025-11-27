"""
AegisAI package initializer.

Currently, this module only exposes the video_processing namespace,
which contains utilities for working with frames and live buffers.
"""

from . import video_processing, vision  # noqa: F401

__all__ = ["video_processing", "vision"]



