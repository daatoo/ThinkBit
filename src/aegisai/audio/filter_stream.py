# src/aegisai/audio/filter_stream.py
from __future__ import annotations

import os
import queue
import subprocess
import tempfile
import threading
import time
from typing import List, Tuple, NamedTuple, Optional

from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.audio.text_buffer import TextBuffer

Interval = Tuple[float, float]


class AudioJob(NamedTuple):
    chunk_id: int
    audio_path: str
    start_ts: float
    duration: float


class AudioResult(NamedTuple):
    chunk_id: int
    # For now we only return empty intervals (no muting),
    # but the structure supports real intervals later.
    intervals: List[Interval]  # ABSOLUTE timestamps in stream timeline


class AudioStreamFilter:
    """
    Streaming audio pipeline.

    Right now this does:
      - Convert chunk media (e.g. mp4) -> 16kHz mono WAV
      - Run STT (transcribe_audio) on that chunk
      - If there is speech, we just log it and return NO mute intervals.

    This is intentionally minimal and consistent with your current code,
    without introducing analyze_text or detect_toxic_segments here.
    """

    def __init__(
        self,
        num_workers: int = 12,
        text_buffer: Optional[TextBuffer] = None,
    ) -> None:
        self.num_workers = num_workers
        self.text_buffer = text_buffer or TextBuffer()

        self.job_q: "queue.Queue[Optional[AudioJob]]" = queue.Queue()
        self.result_q: "queue.Queue[AudioResult]" = queue.Queue()

        self._workers: List[threading.Thread] = []
        self._closed = False

        self._start_workers()

    # ---------------- worker management ----------------
    def _start_workers(self) -> None:
        for i in range(self.num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"AudioStreamWorker-{i}",
                daemon=True,
            )
            t.start()
            self._workers.append(t)

    def _worker_loop(self) -> None:
        while True:
            job = self.job_q.get()
            if job is None:  # stop signal
                self.job_q.task_done()
                break

            try:
                result = self._process_job(job)
                if result is not None:
                    self.result_q.put(result)
            except Exception as e:
                print(f"[AudioStreamFilter] Error processing job {job}: {e}")
            finally:
                self.job_q.task_done()

    # ---------------- core logic ----------------
    def _process_job(self, job: AudioJob) -> Optional[AudioResult]:
        chunk_id = job.chunk_id
        input_media = job.audio_path
        start_ts = job.start_ts
        duration = job.duration

        t0 = time.time()
        print(f"[audio] chunk {chunk_id} START at {t0:.3f}")

        # 0) Convert the input media (e.g. mp4) into a 16kHz mono WAV chunk
        with tempfile.TemporaryDirectory(prefix="aegis_stream_audio_") as tmpdir:
            wav_path = os.path.join(tmpdir, f"chunk_{chunk_id:06d}.wav")

            ff_cmd = [
                "ffmpeg",
                "-y",
                "-i", input_media,
                "-ac", "1",          # mono
                "-ar", "16000",      # 16 kHz
                "-f", "wav",
                wav_path,
            ]
            proc = subprocess.run(
                ff_cmd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if proc.returncode != 0:
                print(
                    f"[audio] chunk {chunk_id} ffmpeg conv failed "
                    f"(code={proc.returncode}): {proc.stderr[:400]}"
                )
                return AudioResult(chunk_id, [])

            # 1) STT
            t_stt0 = time.time()
            try:
                raw = transcribe_audio(wav_path)
            except Exception as e:
                print(
                    f"[audio] chunk {chunk_id} STT failed after "
                    f"{time.time() - t_stt0:.3f}s: {e}"
                )
                return AudioResult(chunk_id, [])
            t_stt1 = time.time()
            print(f"[audio] chunk {chunk_id} STT done in {t_stt1 - t_stt0:.3f}s")

            # 2) Normalize STT result
            transcripts: List[str] = []

            if isinstance(raw, dict):
                transcripts = raw.get("transcripts", []) or []
            elif isinstance(raw, list):
                transcripts = [str(x) for x in raw]
            else:
                transcripts = [str(raw)]

            text = " ".join(transcripts).strip()
            if not text:
                print(
                    f"[audio] chunk {chunk_id} no speech, "
                    f"total {time.time() - t0:.3f}s"
                )
                # No speech -> no mute intervals
                return AudioResult(chunk_id, [])

            # For now, we only log the text.
            # Your file-based moderation logic lives in audio_worker;
            # when you’re ready, you can reuse that logic here.
            print(
                f"[audio] chunk {chunk_id} text='{text[:120]}' "
                f"(len={len(text)}) total={time.time() - t0:.3f}s"
            )

            # TODO: plug in real moderation here if you want muting for streaming.
            # For now, we return an empty list => no muted intervals.
            intervals: List[Interval] = []

            return AudioResult(chunk_id=chunk_id, intervals=intervals)

    # ---------------- public API ----------------
    def submit_chunk(
        self,
        chunk_id: int,
        audio_path: str,
        start_ts: float,
        duration: float,
    ) -> None:
        """
        Submit audio chunk for analysis.
        Called by the pipeline when a new chunk arrives.
        """
        if self._closed:
            raise RuntimeError("AudioStreamFilter is closed")

        job = AudioJob(
            chunk_id=int(chunk_id),
            audio_path=audio_path,
            start_ts=float(start_ts),
            duration=float(duration),
        )
        self.job_q.put(job)

    def get_result_nowait(self) -> Optional[AudioResult]:
        """
        Non-blocking: return next AudioResult if available, else None.
        Used by the pipeline poll loop.
        """
        try:
            return self.result_q.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        """
        Stop workers after all existing jobs finish.
        Call once when stream ends and you've submitted all chunks.
        """
        if self._closed:
            return
        self._closed = True

        for _ in range(self.num_workers):
            self.job_q.put(None)

        for t in self._workers:
            t.join()
