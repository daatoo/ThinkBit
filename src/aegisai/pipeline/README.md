## `src/aegisai/pipeline/` – overview

High-level orchestration layer:

* Describes **what** is being moderated: audio/video, file/stream.
* Calls lower-level modules:

  * `audio.filter_file`, `audio.filter_stream`
  * `video.filter_file`, `video.filter_stream`
  * `video.ffmpeg_edit`, `video.segment`, `video.region_blur`
* Exposes:

  * **File pipeline** → `file_runner.run_file_job() / run_job()`
  * **Streaming pipeline** → `stream_runner.StreamModerationPipeline`
  * **8 presets** → `use_cases.py`

---

## `config.py`

**`PipelineConfig`**

```python
@dataclass(frozen=True)
class PipelineConfig:
    media_type: str      # "audio" | "video"
    mode: str            # "file" | "stream"
    filter_audio: bool
    filter_video: bool
    def validate(self) -> None: ...
```

* `validate()`:

  * `media_type ∈ {"audio", "video"}`
  * `mode ∈ {"file", "stream"}`
  * if `media_type == "audio"` → `filter_video` must be `False`.
* Extra attributes (e.g. `audio_chunk_seconds`, `audio_workers`, …) can be attached and are read via `getattr`.

Used by `file_runner`, `stream_runner`, and `use_cases`.

---

## `file_runner.py`

Implements **single-file moderation**.

**Key dependencies**

* Audio: `audio.filter_file.filter_audio_file`
* Video: `video.filter_file.filter_video_file`
* Media ops:

  * `video.segment.extract_audio_track`
  * `video.ffmpeg_edit.{mute_intervals_in_video, blur_intervals_in_video, blur_and_mute_intervals_in_video}`
  * `video.region_blur.blur_moving_objects_with_intervals`

**Type**

* `Interval = tuple[float, float]` – `[start_sec, end_sec]` on file timeline.

**Helpers (conceptual)**

* Ensure output dirs, normalize interval formats, copy file if no intervals.
* `_analyze_audio_from_video(video_path, tmpdir, chunk_seconds)`:

  * extract audio → run `filter_audio_file(..., output_audio_path=None)` → `List[Interval]`.

**`run_file_job(cfg, input_path, output_path) -> dict`**

* Assumes `cfg.mode == "file"` and valid `media_type`.
* Reads `cfg.audio_chunk_seconds` (default `5`).

Cases:

1. **Audio file** (`media_type="audio"`, `filter_audio=True`)

   * Calls:

     ```python
     filter_audio_file(
         audio_path=input_path,
         output_audio_path=output_path,
         chunk_seconds=audio_chunk_seconds,
     )
     ```
   * Returns:

     ```python
     {"audio_intervals": [...], "video_intervals": None, "output_path": output_path}
     ```

2. **Video file – audio only** (`media_type="video"`, `filter_audio=True`, `filter_video=False`)

   * `audio_intervals = _analyze_audio_from_video(...)`
   * If any → `mute_intervals_in_video(input_path, audio_intervals, output_path)`
   * Else → copy input.
   * Returns `audio_intervals`, `video_intervals=None`.

3. **Video file – video only** (`media_type="video"`, `filter_audio=False`, `filter_video=True`)

   * `video_result = filter_video_file(input_path, output_path=None)`
   * Uses:

     * `video_intervals = video_result["intervals"]`
     * `object_boxes = video_result.get("object_boxes", [])`
     * `sample_fps = video_result.get("sample_fps", 1.0)`
   * If intervals → `blur_moving_objects_with_intervals(input_path, video_intervals, object_boxes, sample_fps, output_path)`
   * Else → copy input.
   * Returns `video_intervals`, `audio_intervals=None`.

4. **Video file – audio + video** (`media_type="video"`, `filter_audio=True`, `filter_video=True`)

   * Runs in parallel (thread pool):

     * `_analyze_audio_from_video(...)`
     * `filter_video_file(input_path, output_path=None)`
   * If any intervals:

     ```python
     blur_and_mute_intervals_in_video(
         video_path=input_path,
         blur_intervals=video_intervals,
         mute_intervals=audio_intervals,
         output_video_path=output_path,
     )
     ```
   * Else → copy input.
   * Returns both interval lists.

If both `filter_audio` and `filter_video` are `False` → `ValueError`.

**`run_job(cfg, input_path_or_stream, output_path) -> dict`**

* Wrapper for **file-only** usage.
* Requires:

  * `cfg.mode == "file"`
  * `input_path_or_stream` is `str`
  * `output_path` given
* Calls `run_file_job(...)`.

---

## `stream_runner.py`

Implements **chunk-based streaming moderation** on top of audio/video stream filters and ffmpeg.

**Deps**

* `AudioStreamFilter, AudioResult` from `audio.filter_stream`
* `VideoStreamFilter, VideoResult` from `video.filter_stream`
* `blur_and_mute_intervals_in_video` from `video.ffmpeg_edit`

**Interval**

* Same `Interval = (start_sec, end_sec)` in absolute stream time; later converted to chunk-local.

### Data structures

**`ChunkDescriptor`**

```python
@dataclass
class ChunkDescriptor:
    chunk_id: int
    start_ts: float      # absolute (sec from stream start)
    duration: float
    video_path: str      # raw chunk mp4
    audio_path: str
```

**`_ChunkState` (internal)**

```python
@dataclass
class _ChunkState:
    desc: ChunkDescriptor
    audio_intervals_abs: list[Interval] | None = None
    video_intervals_abs: list[Interval] | None = None
```

Stored in `self._chunks[chunk_id]` until both results arrive.

**`FilteredChunk`**

```python
@dataclass
class FilteredChunk:
    chunk_id: int
    start_ts: float
    duration: float
    output_path: str      # filtered mp4 chunk
```

Returned to caller.

**Helpers**

* `_clip_to_chunk(intervals, chunk_start, chunk_duration)` → list of local intervals `[0, duration]` intersecting the chunk.
* `_copy_video(src, dst)` → used when chunk has no bad intervals.

---

### `StreamModerationPipeline`

```python
class StreamModerationPipeline:
    def __init__(
        self,
        output_dir: str,
        audio_workers: int = 12,
        video_workers: int = 20,
        sample_fps: float = 1.0,
        ffmpeg_workers: int = 2,
    )
```

* Creates:

  * `AudioStreamFilter(num_workers=audio_workers)`
  * `VideoStreamFilter(num_workers=video_workers, sample_fps=sample_fps)`
  * `self._chunks: dict[int, _ChunkState]`
  * `self._output_q: Queue[FilteredChunk]`
  * `self._ffmpeg_pool: ThreadPoolExecutor(max_workers=ffmpeg_workers)`

**Public API**

* `submit_chunk(desc: ChunkDescriptor) -> None`

  * Registers `_ChunkState` and calls:

    * `audio_filter.submit_chunk(chunk_id, audio_path, start_ts, duration)`
    * `video_filter.submit_chunk(chunk_id, video_path, start_ts, duration)`
* `poll() -> None`

  * Drains `audio_filter.get_result_nowait()` and `video_filter.get_result_nowait()`.
  * For each result, calls `_handle_audio_result` / `_handle_video_result`, then `_maybe_finalize_chunk`.
* `get_ready_chunk_nowait() -> FilteredChunk | None`

  * Pops next `FilteredChunk` from queue if available.
* `close() -> None`

  * Marks closed, calls `audio_filter.close()`, `video_filter.close()`, does one final `poll()`, then waits for all ffmpeg jobs.

**Finalization logic**

`_maybe_finalize_chunk(chunk_id)`:

1. If both `audio_intervals_abs` and `video_intervals_abs` exist:

   * Compute `blur_local`, `mute_local` via `_clip_to_chunk(...)`.
   * Remove chunk from `self._chunks`.
   * Build `out_path = f"{output_dir}/chunk_{chunk_id:06d}_filtered.mp4"`.

2. If both local lists are empty:

   * Schedule `_copy_video(desc.video_path, out_path)` in `self._ffmpeg_pool`.
   * On success, put `FilteredChunk` in `self._output_q`.

3. Else:

   * Schedule:

     ```python
     blur_and_mute_intervals_in_video(
         video_path=desc.video_path,
         blur_intervals=blur_local,
         mute_intervals=mute_local,
         output_video_path=out_path,
     )
     ```
   * Then push `FilteredChunk` to queue.

Errors in ffmpeg/copy jobs are caught and printed.

---

### `create_stream_pipeline(cfg: PipelineConfig, output_dir: str) -> StreamModerationPipeline`

* Requires `cfg.mode == "stream"`.
* Reads optional config:

  * `cfg.audio_workers` (default 12)
  * `cfg.video_workers` (default 20)
  * `cfg.sample_fps` (default 1.0)
  * `cfg.ffmpeg_workers` (default 2)
* Returns a configured `StreamModerationPipeline`.

---

## `use_cases.py`

Defines 8 named `PipelineConfig` presets:

1. `AUDIO_FILE_FILTER`

   * audio file → filtered audio file
   * `("audio", "file", filter_audio=True, filter_video=False)`

2. `AUDIO_STREAM_FILTER`

   * audio stream → filtered audio stream
   * `("audio", "stream", True, False)`

3. `VIDEO_FILE_AUDIO_ONLY`

   * video file → same video, bad audio muted
   * `("video", "file", True, False)`

4. `VIDEO_FILE_VIDEO_ONLY`

   * video file → bad visuals blurred, audio untouched
   * `("video", "file", False, True)`

5. `VIDEO_FILE_AUDIO_VIDEO`

   * video file → both blur + mute
   * `("video", "file", True, True)`

6. `VIDEO_STREAM_AUDIO_ONLY`

   * video stream → only audio muted
   * `("video", "stream", True, False)`

7. `VIDEO_STREAM_VIDEO_ONLY`

   * video stream → only visuals blurred
   * `("video", "stream", False, True)`

8. `VIDEO_STREAM_AUDIO_VIDEO`

   * video stream → blur + mute
   * `("video", "stream", True, True)`

---
