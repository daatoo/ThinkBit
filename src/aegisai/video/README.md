## `src/aegisai/video` – Video moderation & censoring

End-to-end video side of Aegis: sample frames (1–3 FPS), run Vision moderation + object detection, compute unsafe time intervals, apply full-frame or object-level censoring, and reconstruct the video while preserving audio and supporting streaming (5–10 s delay).

---

### `ffmpeg_edit.py`
Time-based blur/mute using FFmpeg + per-frame box blur with OpenCV.

- Types  
  `Interval = Tuple[float, float]` (seconds), `Box = Tuple[int,int,int,int]` (x1,y1,x2,y2).
- `blur_boxes_in_frame(frame, boxes, ksize=75) -> np.ndarray`  
  Clamps boxes to frame; applies Gaussian → median → Gaussian blur to each ROI; writes back in place.
- `blur_and_mute_intervals_in_video(video_path, blur_intervals, mute_intervals, output_video_path)`  
  Single FFmpeg run: center crop + `boxblur` + `overlay` for `blur_intervals`; `volume=0` for `mute_intervals`;  
  cases:
  - both lists empty → `-c copy` (remux),
  - only blur → re-encode video (`libx264`, `ultrafast`, `zerolatency`), copy audio,
  - only mute → copy video, re-encode audio (`aac`),
  - both → apply both filters together.
- `mute_intervals_in_video(video_path, mute_intervals, output_video_path)`  
  No video change (`-c:v copy`), audio muted in given intervals using chained `volume=enable='between(...)':volume=0`, audio re-encoded to `aac`. Empty list → remux.
- `blur_intervals_in_video(video_path, blur_intervals, output_video_path)`  
  Center-region blur only during intervals; video re-encoded (`libx264`, `ultrafast`, `zerolatency`), audio untouched (`-c:a copy`). Empty list → remux.
- `_build_volume_mute_filter(intervals) -> str`  
  Builds `-af` filter chain string for all intervals.

---

### `ffmpeg_extractor.py`
Minimal FFmpeg wrapper to turn video into a frame sequence.

- `FFmpegFrameExtractionError(RuntimeError)` – FFmpeg failure.
- `@dataclass ExtractionResult`  
  `output_paths: List[Path]`, `fps: float`, `duration: Optional[float]`.
- `class FFmpegFrameExtractor(ffmpeg_path="ffmpeg")`  
  - `_ensure_ffmpeg()` – checks binary with `shutil.which`.
  - `extract_frames(video_path, output_dir, fps, overwrite=True, start_time=None, duration=None, image_format="jpg") -> ExtractionResult`  
    Uses FFmpeg with:
    - `-hide_banner -loglevel error`
    - optional `-ss`/`-t`
    - `-vf "fps=<fps>,scale=-1:720"`
    - `-qscale:v 2`
    Outputs `frame_%06d.<image_format>` in `output_dir`. Raises on non-zero return code.

---

### `frame_sampler.py`
Sampling policy (1–3 FPS) + helper for file-based extraction with timestamps.

- `@dataclass SamplingPlan`  
  `source_fps`, `target_fps`, `stride`.
- `class FrameSampler(min_fps=1.0, max_fps=3.0, default_fps=2.0)`  
  - validates bounds (`min_fps > 0`, `max_fps > 0`, `min_fps <= max_fps`, `default_fps` in range),
  - `plan(source_fps) -> SamplingPlan`  
    if `source_fps` ≤ 0 or None → use `default_fps`; clamp to `[min_fps, max_fps]`;  
    `stride = max(int(round(source_fps / target_fps)), 1)` when downsampling; `target_fps = source_fps / stride`.
  - `should_emit(frame_index, plan) -> bool`  
    `frame_index >= 0`, returns `frame_index % plan.stride == 0`.
- `FrameInfo = Tuple[str, float]` – `(frame_path, timestamp_seconds)`.
- `extract_sampled_frames_from_file(video_path, output_dir, fps=1.0) -> List[FrameInfo]`  
  Uses `FFmpegFrameExtractor.extract_frames`; returns list of `(path, idx / result.fps)`.

---

### `filter_file.py`
Offline (file) video moderation: sample frames, run Vision, compute unsafe intervals + per-frame object boxes.

- Imports:
  - `extract_sampled_frames_from_file` (frame sampling),
  - `analyze_frame_moderation`, `FrameModerationResult` (Vision Safe Search),
  - `intervals_from_frames` (frame decisions → intervals),
  - `merge_intervals` (merge overlapping),
  - `localize_objects_from_path` (object detection, returns `.bbox`).
- Types  
  `Interval = Tuple[float,float]`.
- `_blur_intervals_in_video(video_path, intervals, output_video_path)`  
  Legacy full-frame blur using center crop + `boxblur` with `enable='between(...)'`, audio copied, `libx264` + `-preset ultrafast -tune zerolatency`. Empty intervals → remux.
- `filter_video_file(input_path, output_path, sample_fps=1.0, max_workers=None) -> Dict[str, Any]`  
  Steps:
  1. Check `input_path` exists.
  2. Temp dir for frames.
  3. `extract_sampled_frames_from_file(..., fps=sample_fps)` → list of `(frame_path, ts)`.
  4. `max_workers = min(20, len(frames))` if None.
  5. Moderation: `ThreadPoolExecutor`, each frame → `analyze_frame_moderation(frame_path, timestamp=ts)`; gather `FrameModerationResult`s.
  6. `frame_step = 1.0 / sample_fps`; `raw_intervals = intervals_from_frames(results, frame_step)`; `merged = merge_intervals(raw_intervals)`.
  7. Object boxes: for each `(frame_path, ts)` → `objs = localize_objects_from_path(frame_path)`; `boxes = [obj.bbox for obj in objs]`; if any, append:
     ```python
     {"timestamp": ts, "boxes": boxes}
     ```
  8. Return:
     ```python
     {
       "intervals": merged,
       "object_boxes": per_frame_boxes,
       "sample_fps": sample_fps,
       "output_path": output_path,
     }
     ```
  No blurring is done here; only metadata is produced.

---

### `filter_stream.py`
Streaming version: chunk-based moderation with background worker threads.

- Types  
  `Interval = Tuple[float,float]`.
- `class VideoJob(NamedTuple)`  
  `chunk_id: int`, `video_path: str`, `start_ts: float`, `duration: float`.
- `class VideoResult(NamedTuple)`  
  `chunk_id: int`, `intervals: List[Interval]` (absolute timestamps).
- `class VideoStreamFilter(sample_fps=1.0, num_workers=20)`  
  - Attributes:
    - `sample_fps`,
    - `num_workers`,
    - `job_q: queue.Queue[Optional[VideoJob]]`,
    - `result_q: queue.Queue[VideoResult]`,
    - `_workers: List[threading.Thread]`,
    - `_closed: bool`.
  - `_start_workers()` – spawns `num_workers` daemon threads with `_worker_loop`.
  - `_worker_loop()` – gets `VideoJob` from `job_q`, breaks on `None`, calls `_process_job`, puts `VideoResult` into `result_q`, `task_done()` on each.
  - `_process_job(job) -> Optional[VideoResult]`  
    1. Temp dir `aegis_video_chunk_*`.
    2. `frames = extract_sampled_frames_from_file(...)` at `self.sample_fps`.
    3. If no frames → `VideoResult(chunk_id, [])`.
    4. Moderation with `ThreadPoolExecutor` (`max_workers = min(20, len(frames))`) calling `analyze_frame_moderation(frame_path, timestamp=ts_local)`.
    5. `frame_step = 1.0 / sample_fps`, `raw_local = intervals_from_frames(results, frame_step)`, `merged_local = merge_intervals(raw_local)`.
    6. Shift to absolute: `merged_abs = [(s+start_ts, e+start_ts) for (s,e) in merged_local]`.
    7. Return `VideoResult(chunk_id, merged_abs)`.
  - `submit_chunk(chunk_id, video_path, start_ts, duration)`  
    Raises if closed; otherwise puts `VideoJob` in `job_q`.
  - `get_result_nowait() -> Optional[VideoResult]`  
    Returns next `VideoResult` or `None` if queue empty.
  - `close()`  
    Sets `_closed`, enqueues `None` per worker, joins all threads.

---

### `frame_reconstruction.py`
Region-level censoring (PIL) + FFmpeg reconstruction from processed frames and optional audio.

- Exceptions  
  `ReconstructionError(RuntimeError)`.
- `class CensorEffectType(str, Enum)`  
  `BLUR`, `PIXELATE`, `BLACK_BOX`.
- `@dataclass(frozen=True) CensorInstruction`  
  - `effect_type: CensorEffectType`
  - `start_time: float`, `end_time: float`
  - `x: int`, `y: int`, `width: int`, `height: int`
  - `intensity: float = 12.0`
  - `color: tuple[int,int,int] = (0,0,0)`
  - `active_at(timestamp) -> bool`: `start_time <= t <= end_time`.
- `@dataclass class ReconstructionResult`  
  `output_path: Path`, `frame_count: int`, `fps: float`, `applied_effects: int`.
- `class FrameReconstructionPipeline(ffmpeg_path="ffmpeg")`  
  - `_ensure_ffmpeg()` – checks binary.
  - `reconstruct(frames_dir, output_path, fps, instructions=None, audio_path=None, image_format="jpg") -> ReconstructionResult`  
    1. Ensure `fps > 0`, `instructions` default `[]`.
    2. Resolve paths, list frames `*.image_format`; raise if none.
    3. Temp dir `processed_frames_*`.
    4. `_process_frames(frame_paths, processed_dir, fps, instructions) -> int`  
       - For each frame `index`:
         - open via PIL, convert to `"RGB"`,
         - compute `timestamp = index / fps`,
         - collect `active = [instr for instr in instructions if instr.active_at(timestamp)]`,
         - if any, call `apply_effects(image, active)` and increment `applied` by `len(active)`,
         - save result with original filename into `processed_dir`.
    5. Renumber processed frames sequentially as `frame_%06d.<image_format>`.
    6. Run FFmpeg:
       - `-framerate fps`
       - `-i frame_%06d.<image_format>`
       - if `audio_path`:
         - `-i audio_path`, `-c:a aac`, `-shortest`
       - `-c:v libx264 -pix_fmt yuv420p output_path`.
    7. On non-zero exit, raise with stderr; else return `ReconstructionResult`.
  - `apply_effects(image, instructions) -> Image.Image`  
    Copies input; for each instruction calls `_apply_effect`; returns modified.
  - `_apply_effect(image, instruction)`  
    - Clamp box to image bounds; noop if invalid.
    - Crop `region = image.crop((x1,y1,x2,y2))`.
    - If `BLUR`: `GaussianBlur(radius=max(intensity,1))`.
    - If `PIXELATE`: block = `max(int(intensity),2)`; downscale to `(down_w, down_h)` using `NEAREST`, then upscale back.
    - If `BLACK_BOX`: `Image.new("RGB", (w,h), instruction.color)`.
    - Paste region back.

---

### `live_buffer.py`
Time-based rolling buffer for live streams; ensures 5–10 s delay window.

- `@dataclass class BufferedFrame`  
  `timestamp: float`, `payload: Any`, `metadata: dict[str,Any] = {}`.
- `class LiveFrameBuffer(delay_seconds=5.0, max_delay_seconds=10.0)`  
  - Constructor:
    - `5 <= delay_seconds <= 10`, `max_delay_seconds >= delay_seconds`,
    - maintains `_buffer: Deque[BufferedFrame]`.
  - `push(frame: BufferedFrame)`  
    Validates `frame.timestamp >= 0`, appends, then `_trim_buffer()`.
  - `pop_ready(now: float) -> List[BufferedFrame]`  
    Pops from left while `now - first.timestamp >= delay_seconds`; trims buffer; returns popped list.
  - `_trim_buffer()`  
    While `_buffer` non-empty and `(last.timestamp - first.timestamp) > max_delay_seconds`, drop left.
  - `__len__(self) -> int`  
    Number of buffered frames.

---

### `region_blur.py`
Object-level blur applied only inside unsafe time intervals; merges blurred video with original audio.

- Types  
  `Interval = Tuple[float,float]`, `Box = Tuple[int,int,int,int]`.
- `_timestamp_in_intervals(ts, intervals) -> bool`  
  Returns `True` if any `[start,end]` contains `ts`.
- `_build_sample_lookup(object_boxes) -> Dict[float, List[Box]]`  
  Converts:
  ```python
  [{"timestamp": ts, "boxes": [(x1,y1,x2,y2), ...]}, ...]
  ```
  to:
  ```python
    {round(ts,3): [boxes...], ...}
  ```

skipping empty lists.

* `blur_moving_objects_with_intervals(video_path, intervals, object_boxes, sample_fps, output_video_path, blur_ksize=35)`

  1. Resolve `video_path`, `output_video_path`. If `intervals` empty → `shutil.copy2`.
  2. Build `sample_lookup` via `_build_sample_lookup`.
  3. Open video with `cv2.VideoCapture`; read `fps`, `width`, `height`, `frame_count`.
  4. Temp dir `aegis_objblur_*`, create `VideoWriter` (`mp4v`, same `fps`, size).
  5. For each frame index:

     * read frame; break on end.
     * `ts = frame_idx / fps`.
     * if `_timestamp_in_intervals(ts, intervals)`:

       * `sample_index = int(round(ts * sample_fps))`,
       * `sample_ts = sample_index / sample_fps`,
       * `key = round(sample_ts, 3)`,
       * `boxes = sample_lookup.get(key, [])`,
       * if boxes → `frame = blur_boxes_in_frame(frame, boxes, ksize=blur_ksize)`.
     * `out.write(frame)`, increment `frame_idx`.
  6. Release `cap`, `out`.
  7. Merge original audio with blurred video via FFmpeg:

     * `-i video_blurred_noaudio.mp4`, `-i original`,
     * `-map 0:v:0 -map 1:a:0?`,
     * `-c:v copy -c:a copy -shortest output_video_path`.
       Raises on failure.

---

### `segment.py`

Audio extraction + segmentation helpers (used for STT side).

* `extract_audio_chunks_from_video(video_path, output_dir, chunk_seconds, prefix="chunk_") -> List[str]`

  * Validates `video_path` exists; `os.makedirs(output_dir, exist_ok=True)`.
  * `out_pattern = <output_dir>/<prefix>%05d.wav`.
  * FFmpeg command:

    * `-y -i video_path -vn -ac 1 -ar 16000 -f segment -segment_time chunk_seconds -reset_timestamps 1 out_pattern`.
  * On `CalledProcessError` → raise `RuntimeError`.
  * Returns sorted list of `chunk_*.wav` using `glob.glob`.
* `extract_audio_track(video_path, audio_out_path)`

  * FFmpeg: `-y -i video_path -vn -ac 1 -ar 16000 audio_out_path`.
  * Extracts full mono 16 kHz audio (e.g., for STT).

---

