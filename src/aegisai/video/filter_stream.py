# src/aegisai/video/filter_stream.py
from __future__ import annotations

import queue
import threading
from typing import List, Tuple, NamedTuple, Optional
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor

from src.aegisai.video.frame_sampler import extract_sampled_frames_from_file
from src.aegisai.vision.safe_search import (
    analyze_frame_moderation,
    FrameModerationResult,
)
from src.aegisai.vision.vision_rules import intervals_from_frames
from src.aegisai.audio.intervals import merge_intervals  # or video.merge_intervals

Interval = Tuple[float, float]


class VideoJob(NamedTuple):
    chunk_id: int
    video_path: str
    start_ts: float
    duration: float


class VideoResult(NamedTuple):
    chunk_id: int
    intervals: List[Interval]  # ABSOLUTE timestamps to blur


class VideoStreamFilter:
    """
    Streaming video moderation.

    - Worker threads wait on job_q.
    - For each chunk:
        * sample frames
        * run analyze_frame_moderation(...)
        * frame decisions -> unsafe LOCAL intervals
        * merge + shift to ABSOLUTE times
        * push VideoResult(chunk_id, intervals) to result_q.
    """

    def __init__(
        self,
        sample_fps: float = 1.0,
        num_workers: int = 20,
    ) -> None:
        self.sample_fps = sample_fps
        self.num_workers = num_workers

        self.job_q: "queue.Queue[Optional[VideoJob]]" = queue.Queue()
        self.result_q: "queue.Queue[VideoResult]" = queue.Queue()

        self._workers: List[threading.Thread] = []
        self._closed = False

        self._start_workers()

    # ---------------- worker management ----------------
    def _start_workers(self) -> None:
        for i in range(self.num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"VideoStreamWorker-{i}",
                daemon=True,
            )
            t.start()
            self._workers.append(t)

    def _worker_loop(self) -> None:
        while True:
            job = self.job_q.get()
            if job is None:
                self.job_q.task_done()
                break

            try:
                result = self._process_job(job)
                if result is not None:
                    self.result_q.put(result)
            except Exception as e:
                print(f"[VideoStreamFilter] Error processing job {job}: {e}")
            finally:
                self.job_q.task_done()

    # ---------------- core logic (based on filter_video_file) ----------------
    def _process_job(self, job: VideoJob) -> Optional[VideoResult]:
        chunk_id = job.chunk_id
        video_path = job.video_path
        start_ts = job.start_ts
        sample_fps = self.sample_fps

        frame_step = 1.0 / sample_fps

        with TemporaryDirectory(prefix="aegis_video_chunk_") as tmpdir:
            # 1) Sample frames
            frames = extract_sampled_frames_from_file(
                video_path=video_path,
                output_dir=tmpdir,
                fps=sample_fps,
            )
            print(
                f"[VideoStreamFilter] Chunk {chunk_id}: "
                f"extracted {len(frames)} frames at {sample_fps} FPS"
            )

            if not frames:
                return VideoResult(chunk_id, [])

            # 2) Analyze frames in parallel
            max_workers = min(20, len(frames))
            results: List[FrameModerationResult] = []

            def _moderate_one(frame_path: str, ts_local: float) -> FrameModerationResult:
                return analyze_frame_moderation(frame_path, timestamp=ts_local)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(_moderate_one, frame_path, ts)
                    for (frame_path, ts) in frames
                ]
                for fut in futures:
                    results.append(fut.result())

            # 3) LOCAL intervals
            raw_local = intervals_from_frames(results, frame_step=frame_step)
            merged_local = merge_intervals(raw_local)

            # 4) Shift to ABSOLUTE
            merged_abs: List[Interval] = [
                (s + start_ts, e + start_ts) for (s, e) in merged_local
            ]

            print(
                f"[VideoStreamFilter] Chunk {chunk_id}: "
                f"unsafe local={merged_local}, abs={merged_abs}"
            )

            return VideoResult(chunk_id=chunk_id, intervals=merged_abs)

    # ---------------- public API ----------------
    def submit_chunk(
        self,
        chunk_id: int,
        video_path: str,
        start_ts: float,
        duration: float,
    ) -> None:
        if self._closed:
            raise RuntimeError("VideoStreamFilter is closed")

        job = VideoJob(
            chunk_id=int(chunk_id),
            video_path=video_path,
            start_ts=float(start_ts),
            duration=float(duration),
        )
        self.job_q.put(job)

    def get_result_nowait(self) -> Optional[VideoResult]:
        try:
            return self.result_q.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        for _ in range(self.num_workers):
            self.job_q.put(None)

        for t in self._workers:
            t.join()
