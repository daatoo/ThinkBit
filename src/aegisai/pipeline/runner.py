# src/aegisai/pipeline/runner.py
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any, Optional

from src.aegisai.pipeline.config import PipelineConfig
from src.aegisai.audio.filter_file import filter_audio_file
from src.aegisai.video.filter_file import filter_video_file
from src.aegisai.video.ffmpeg_edit import mute_intervals_in_video, blur_and_mute_intervals_in_video, blur_intervals_in_video
import concurrent.futures
from src.aegisai.video.segment import extract_audio_track
from typing import List, Tuple

from src.aegisai.audio.filter_stream import AudioStreamFilter, AudioResult
from src.aegisai.video.filter_stream import VideoStreamFilter, VideoResult
from src.aegisai.video.ffmpeg_edit import blur_and_mute_intervals_in_video

import os
from typing import NamedTuple, List, Dict, Tuple, Iterable

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
                Run video moderation, return blur intervals.
                Assumes filter_video_file returns either:
                  - dict with 'intervals' key, or
                  - directly a list of intervals.
                Also assumes we can pass output_path=None to do analysis-only.
                """
                video_result = filter_video_file(input_path, output_path=None)

                if isinstance(video_result, dict) and "intervals" in video_result:
                    return video_result["intervals"]

                # fallback if it's already a list
                return video_result

            # Run audio + video analysis in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                audio_future = executor.submit(audio_job)
                video_future = executor.submit(video_job)

                audio_intervals = audio_future.result()
                video_intervals = video_future.result()

            # Single ffmpeg: blur + mute together
            blur_and_mute_intervals_in_video(
                video_path=input_path,
                blur_intervals=video_intervals,
                mute_intervals=audio_intervals,
                output_video_path=output_path,
            )

        return {
            "audio_intervals": audio_intervals,
            "video_intervals": video_intervals,
            "output_path": output_path,
        }

    raise ValueError("File pipeline with neither audio nor video filtering is meaningless.")


def _run_stream_job(
    cfg: PipelineConfig,
    input_stream: Any,
) -> Any:
    return True




import os
import queue
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from src.aegisai.audio.filter_stream import AudioStreamFilter, AudioResult
from src.aegisai.video.filter_stream import VideoStreamFilter, VideoResult
from src.aegisai.video.ffmpeg_edit import blur_and_mute_intervals_in_video

Interval = Tuple[float, float]


@dataclass
class ChunkDescriptor:
    chunk_id: int
    start_ts: float
    duration: float
    video_path: str
    audio_path: str


@dataclass
class _ChunkState:
    desc: ChunkDescriptor
    audio_intervals_abs: Optional[List[Interval]] = None
    video_intervals_abs: Optional[List[Interval]] = None


@dataclass
class FilteredChunk:
    chunk_id: int
    start_ts: float
    duration: float
    output_path: str


def _clip_to_chunk(
    intervals: List[Interval],
    chunk_start: float,
    chunk_duration: float,
) -> List[Interval]:
    """Convert ABSOLUTE intervals to LOCAL intervals inside this chunk."""
    chunk_end = chunk_start + chunk_duration
    local: List[Interval] = []

    for s_abs, e_abs in intervals:
        if e_abs <= chunk_start or s_abs >= chunk_end:
            continue
        s_loc = max(0.0, s_abs - chunk_start)
        e_loc = min(chunk_duration, e_abs - chunk_start)
        if e_loc > s_loc:
            local.append((s_loc, e_loc))

    return local


class StreamModerationPipeline:
    """
    Orchestrates streaming moderation:

    - `submit_chunk(desc)` is called as each new 1s/1.5s chunk appears.
    - Internally:
        * sends audio part to AudioStreamFilter
        * sends video part to VideoStreamFilter
    - `poll()` pulls available AudioResult / VideoResult, pairs them by chunk_id.
    - When both audio+video intervals exist for a chunk:
        * convert to LOCAL intervals
        * run blur_and_mute_intervals_in_video
        * push FilteredChunk into output queue.

    The upper layer (WebRTC/HTTP/etc.) periodically calls:
        pipeline.poll()
        pipeline.get_ready_chunk_nowait()  # to send to client
    """

    def __init__(
        self,
        output_dir: str,
        audio_workers: int = 12,
        video_workers: int = 20,
        sample_fps: float = 1.0,
    ) -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.audio_filter = AudioStreamFilter(num_workers=audio_workers)
        self.video_filter = VideoStreamFilter(
            num_workers=video_workers,
            sample_fps=sample_fps,
        )

        self._chunks: Dict[int, _ChunkState] = {}
        self._output_q: "queue.Queue[FilteredChunk]" = queue.Queue()
        self._closed = False

    # ------------- public: submit + poll + get output -------------
    def submit_chunk(self, desc: ChunkDescriptor) -> None:
        """
        Called once per new chunk (e.g. every 1s or 1.5s).

        This does not block. It just enqueues work in audio/video modules.
        """
        if self._closed:
            raise RuntimeError("StreamModerationPipeline is closed")

        self._chunks[desc.chunk_id] = _ChunkState(desc=desc)

        # submit to audio
        self.audio_filter.submit_chunk(
            chunk_id=desc.chunk_id,
            audio_path=desc.audio_path,
            start_ts=desc.start_ts,
            duration=desc.duration,
        )

        # submit to video
        self.video_filter.submit_chunk(
            chunk_id=desc.chunk_id,
            video_path=desc.video_path,
            start_ts=desc.start_ts,
            duration=desc.duration,
        )

    def poll(self) -> None:
        """
        Non-blocking: pull any available results from audio & video modules,
        update chunk states, and finalize chunks whose audio+video are both ready.
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
        """
        if self._closed:
            return
        self._closed = True

        # Tell modules to finish
        self.audio_filter.close()
        self.video_filter.close()

        # One last poll to flush any remaining results
        self.poll()

    # ------------- internal handlers -------------
    def _handle_audio_result(self, res: AudioResult) -> None:
        st = self._chunks.get(res.chunk_id)
        if st is None:
            # Chunk not known? create shell state (should not normally happen)
            st = _ChunkState(
                desc=ChunkDescriptor(
                    chunk_id=res.chunk_id,
                    start_ts=0.0,
                    duration=0.0,
                    video_path="",
                    audio_path="",
                )
            )
            self._chunks[res.chunk_id] = st

        st.audio_intervals_abs = res.intervals
        self._maybe_finalize_chunk(st)

    def _handle_video_result(self, res: VideoResult) -> None:
        st = self._chunks.get(res.chunk_id)
        if st is None:
            st = _ChunkState(
                desc=ChunkDescriptor(
                    chunk_id=res.chunk_id,
                    start_ts=0.0,
                    duration=0.0,
                    video_path="",
                    audio_path="",
                )
            )
            self._chunks[res.chunk_id] = st

        st.video_intervals_abs = res.intervals
        self._maybe_finalize_chunk(st)

    def _maybe_finalize_chunk(self, st: _ChunkState) -> None:
        """
        If both audio+video intervals exist for this chunk, run ffmpeg and
        push FilteredChunk into output queue.
        """
        if st.audio_intervals_abs is None or st.video_intervals_abs is None:
            return  # still waiting for the other side

        desc = st.desc
        blur_abs = st.video_intervals_abs
        mute_abs = st.audio_intervals_abs

        blur_local = _clip_to_chunk(
            blur_abs, desc.start_ts, desc.duration
        )
        mute_local = _clip_to_chunk(
            mute_abs, desc.start_ts, desc.duration
        )

        out_path = os.path.join(
            self.output_dir,
            f"chunk_{desc.chunk_id:06d}_filtered.mp4",
        )

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

        # optional: free memory
        # del self._chunks[desc.chunk_id]