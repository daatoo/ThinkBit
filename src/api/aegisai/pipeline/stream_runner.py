from __future__ import annotations

import os
import shutil
import queue
import threading
import concurrent.futures
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any

from src.aegisai.audio.filter_stream import AudioStreamFilter, AudioResult
from src.aegisai.video.filter_stream import VideoStreamFilter, VideoResult
from src.aegisai.video.ffmpeg_edit import blur_and_mute_intervals_in_video
from src.aegisai.pipeline.config import PipelineConfig

Interval = Tuple[float, float]


# -------------------------------------------------------------------
# Dataclasses for streaming
# -------------------------------------------------------------------

@dataclass
class ChunkDescriptor:
    """
    Metadata for a single incoming chunk.

    All times are in seconds, absolute on the global stream timeline.
    """
    chunk_id: int
    start_ts: float
    duration: float
    video_path: str
    audio_path: str


@dataclass
class _ChunkState:
    """Internal state for a chunk while waiting for audio+video results."""
    desc: ChunkDescriptor
    audio_intervals_abs: Optional[List[Interval]] = None
    video_intervals_abs: Optional[List[Interval]] = None


@dataclass
class FilteredChunk:
    """Result of processing a chunk: path to the filtered MP4 segment."""
    chunk_id: int
    start_ts: float
    duration: float
    output_path: str


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _clip_to_chunk(
    intervals: List[Interval],
    chunk_start: float,
    chunk_duration: float,
) -> List[Interval]:
    """
    Convert ABSOLUTE intervals (seconds from stream start) to LOCAL intervals
    within a chunk.

    Returns a list of (start_local, end_local) in [0, chunk_duration].
    """
    chunk_end = chunk_start + chunk_duration
    local: List[Interval] = []

    for s_abs, e_abs in intervals:
        # completely before or after this chunk
        if e_abs <= chunk_start or s_abs >= chunk_end:
            continue

        s_loc = max(0.0, s_abs - chunk_start)
        e_loc = min(chunk_duration, e_abs - chunk_start)
        if e_loc > s_loc:
            local.append((float(s_loc), float(e_loc)))

    return local


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _copy_video(src_path: str, dst_path: str) -> None:
    """
    Cheap "safe" operation for chunks with no bad intervals.
    We just copy the original chunk file.

    Assumes src_path is a valid small MP4 chunk file.
    """
    _ensure_dir(os.path.dirname(os.path.abspath(dst_path)))
    shutil.copy2(src_path, dst_path)


# -------------------------------------------------------------------
# Stream moderation pipeline
# -------------------------------------------------------------------

class StreamModerationPipeline:
    """
    Orchestrates streaming moderation on top of file chunks.

    Typical usage (pseudocode):

        pipeline = StreamModerationPipeline(output_dir="...")

        for each new chunk (id, start_ts, duration, video_path, audio_path):
            pipeline.submit_chunk(ChunkDescriptor(...))

            # periodically:
            pipeline.poll()
            while True:
                out_chunk = pipeline.get_ready_chunk_nowait()
                if out_chunk is None:
                    break
                # send out_chunk.output_path to client / muxer

        # when stream ends:
        pipeline.close()
        # then drain remaining ready chunks from get_ready_chunk_nowait()

    Concurrency model:
        - submit_chunk(), poll(), and close() are expected to be called
          from one "control" thread.
        - get_ready_chunk_nowait() is thread-safe and can be called
          from another thread if needed.
    """

    def __init__(
        self,
        output_dir: str,
        audio_workers: int = 12,
        video_workers: int = 20,
        sample_fps: float = 1.0,
        ffmpeg_workers: int = 2,
    ) -> None:
        self.output_dir = output_dir
        _ensure_dir(self.output_dir)

        self.audio_filter = AudioStreamFilter(num_workers=audio_workers)
        self.video_filter = VideoStreamFilter(
            num_workers=video_workers,
            sample_fps=sample_fps,
        )

        self._chunks: Dict[int, _ChunkState] = {}
        self._output_q: "queue.Queue[FilteredChunk]" = queue.Queue()

        self._lock = threading.Lock()
        self._closed = False

        # Small pool for ffmpeg / copy work so poll() stays non-blocking.
        self._ffmpeg_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=ffmpeg_workers
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_chunk(self, desc: ChunkDescriptor) -> None:
        """
        Called once per new chunk (e.g. every 1s or 1.5s).

        This does not block; it just enqueues work in audio/video modules.
        """
        if self._closed:
            raise RuntimeError("StreamModerationPipeline is closed; cannot submit new chunks.")

        with self._lock:
            if desc.chunk_id in self._chunks:
                raise ValueError(f"Chunk {desc.chunk_id} already exists in pipeline.")
            self._chunks[desc.chunk_id] = _ChunkState(desc=desc)

        # submit to audio worker pool
        self.audio_filter.submit_chunk(
            chunk_id=desc.chunk_id,
            audio_path=desc.audio_path,
            start_ts=desc.start_ts,
            duration=desc.duration,
        )

        # submit to video worker pool
        self.video_filter.submit_chunk(
            chunk_id=desc.chunk_id,
            video_path=desc.video_path,
            start_ts=desc.start_ts,
            duration=desc.duration,
        )

    def poll(self) -> None:
        """
        Non-blocking: pull any available results from audio & video modules,
        update chunk states, and finalize chunks whose audio+video intervals
        are both ready.

        Safe to call frequently (e.g. on a timer or after each submitted chunk).
        """
        # Drain all available audio results
        while True:
            res: Optional[AudioResult] = self.audio_filter.get_result_nowait()
            if res is None:
                break
            self._handle_audio_result(res)

        # Drain all available video results
        while True:
            res: Optional[VideoResult] = self.video_filter.get_result_nowait()
            if res is None:
                break
            self._handle_video_result(res)

    def get_ready_chunk_nowait(self) -> Optional[FilteredChunk]:
        """
        Non-blocking: return next filtered chunk if available, else None.
        """
        try:
            return self._output_q.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        """
        Called when the incoming stream ends and no more chunks will arrive.

        This:
          - closes audio/video worker pools
          - performs one final poll()
          - waits for all ffmpeg/copy work to finish
        """
        if self._closed:
            return
        self._closed = True

        # Tell worker modules to finish.
        self.audio_filter.close()
        self.video_filter.close()

        # One last poll to flush any remaining intervals into ffmpeg jobs.
        self.poll()

        # Wait for all ffmpeg / copy tasks to complete.
        self._ffmpeg_pool.shutdown(wait=True)

        # Any chunks left with only audio OR video intervals are simply dropped;
        # typically this only happens if the stream ended mid-chunk.

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _handle_audio_result(self, res: AudioResult) -> None:
        """
        Attach audio intervals to the corresponding chunk, then try to finalize it.
        """
        chunk_id = res.chunk_id

        with self._lock:
            st = self._chunks.get(chunk_id)
            if st is None:
                # Unknown chunk (e.g., late result after close). Drop safely.
                # You can replace this with logging if desired.
                # print(f"[StreamModerationPipeline] Dropped audio result for unknown chunk {chunk_id}")
                return

            st.audio_intervals_abs = list(res.intervals or [])
            # Don't finalize while holding lock; just remember which chunk to check.
        self._maybe_finalize_chunk(chunk_id)

    def _handle_video_result(self, res: VideoResult) -> None:
        """
        Attach video intervals to the corresponding chunk, then try to finalize it.
        """
        chunk_id = res.chunk_id

        with self._lock:
            st = self._chunks.get(chunk_id)
            if st is None:
                # Unknown chunk; drop safely.
                # print(f"[StreamModerationPipeline] Dropped video result for unknown chunk {chunk_id}")
                return

            st.video_intervals_abs = list(res.intervals or [])
        self._maybe_finalize_chunk(chunk_id)

    def _maybe_finalize_chunk(self, chunk_id: int) -> None:
        """
        If both audio+video intervals exist for this chunk, compute local
        intervals, schedule ffmpeg/copy work, and enqueue a FilteredChunk.
        """
        with self._lock:
            st = self._chunks.get(chunk_id)
            if (
                st is None
                or st.audio_intervals_abs is None
                or st.video_intervals_abs is None
            ):
                # Not ready yet.
                return

            desc = st.desc

            # Compute local intervals (within this chunk).
            blur_local = _clip_to_chunk(
                st.video_intervals_abs,
                desc.start_ts,
                desc.duration,
            )
            mute_local = _clip_to_chunk(
                st.audio_intervals_abs,
                desc.start_ts,
                desc.duration,
            )

            # We won't need this chunk's state anymore; we capture everything
            # needed in local variables and remove from the dict.
            del self._chunks[chunk_id]

        # Lock released here. Heavy work (ffmpeg/copy) is done outside the lock.

        out_path = os.path.join(
            self.output_dir,
            f"chunk_{desc.chunk_id:06d}_filtered.mp4",
        )

        # If there is nothing to blur or mute, avoid ffmpeg and just copy.
        if not blur_local and not mute_local:
            def copy_job() -> None:
                try:
                    _copy_video(desc.video_path, out_path)
                    filtered = FilteredChunk(
                        chunk_id=desc.chunk_id,
                        start_ts=desc.start_ts,
                        duration=desc.duration,
                        output_path=out_path,
                    )
                    self._output_q.put(filtered)
                except Exception as e:
                    # Replace with logging if desired
                    print(f"[StreamModerationPipeline] Error copying safe chunk {desc.chunk_id}: {e}")

            self._ffmpeg_pool.submit(copy_job)
            return

        # Otherwise run one ffmpeg command to blur + mute this chunk.
        def ffmpeg_job() -> None:
            try:
                blur_and_mute_intervals_in_video(
                    video_path=desc.video_path,
                    blur_intervals=blur_local,
                    mute_intervals=mute_local,
                    output_video_path=out_path,
                )
                filtered = FilteredChunk(
                    chunk_id=desc.chunk_id,
                    start_ts=desc.start_ts,
                    duration=desc.duration,
                    output_path=out_path,
                )
                self._output_q.put(filtered)
            except Exception as e:
                # Replace with logging if desired
                print(f"[StreamModerationPipeline] Error processing chunk {desc.chunk_id}: {e}")

        self._ffmpeg_pool.submit(ffmpeg_job)


# -------------------------------------------------------------------
# Optional convenience factory
# -------------------------------------------------------------------

def create_stream_pipeline(
    cfg: PipelineConfig,
    output_dir: str,
) -> StreamModerationPipeline:
    """
    Helper to build a StreamModerationPipeline from PipelineConfig.

    Expects:
        cfg.mode == "stream"
        cfg.media_type == "video" (or "audio+video" conceptually)

    You can extend PipelineConfig with:
        - audio_workers
        - video_workers
        - sample_fps
        - ffmpeg_workers
    and they will be picked up if present.
    """
    if getattr(cfg, "mode", None) != "stream":
        raise ValueError("create_stream_pipeline expects cfg.mode == 'stream'")

    # Defaults, overridden by cfg if present
    audio_workers = int(getattr(cfg, "audio_workers", 12))
    video_workers = int(getattr(cfg, "video_workers", 20))
    sample_fps = float(getattr(cfg, "sample_fps", 1.0))
    ffmpeg_workers = int(getattr(cfg, "ffmpeg_workers", 2))

    return StreamModerationPipeline(
        output_dir=output_dir,
        audio_workers=audio_workers,
        video_workers=video_workers,
        sample_fps=sample_fps,
        ffmpeg_workers=ffmpeg_workers,
    )
