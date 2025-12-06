# `src/aegisai/` – AegisAI Core Moderation Engine

AegisAI is a **media moderation engine** for audio & video.

It takes **files or live streams**, runs them through:

* **Google Speech-to-Text** (audio profanity)
* **Google Vision SafeSearch + label detection** (nudity / racy / violence)
* Custom **text rules** and **interval logic**

…and outputs **censored media**:

* Audio: toxic segments **muted**
* Video: unsafe visuals **blurred** (full-frame or object-level)
* Streaming: same logic, but chunk-based with a small delay (5–10 seconds).

This package contains the **core logic only** – no web API, no UI. It’s meant to be called from your own backend / CLI.

---

## High-level architecture

At the top, the **pipeline** module decides:

* What kind of media? → `audio` or `video`
* How do we process it? → `file` or `stream`
* Which sides are active? → audio filtering and/or video filtering

Underneath, it delegates to 4 specialized submodules:

* [`audio`](./audio/) – STT + audio profanity → mute intervals
* [`video`](./video/) – Vision moderation + object blur → blur intervals
* [`vision`](./vision/) – Google Vision wrappers & rules
* [`moderation`](./moderation/) – shared profanity vocab + text rules

The typical flow for a **video file** (audio + video filtering):

1. **Video → audio chunks** (`video.segment.extract_audio_chunks_from_video`)
2. **Audio chunks → STT words** (`audio.speech_to_text.transcribe_audio`)
3. **Words + text rules → mute intervals** (`audio.intervals.detect_toxic_segments`)
4. **Sampled frames → Vision SafeSearch/labels** (`vision.safe_search.analyze_frame_moderation`)
5. **Frame decisions → blur intervals** (`vision.vision_rules.intervals_from_frames`)
6. **Intervals → final censored video** (`video.ffmpeg_edit.blur_and_mute_intervals_in_video`
   or `video.region_blur.blur_moving_objects_with_intervals`)

The pipeline glues all of this together and exposes a **simple API**.

---

## Modules

### 1. `audio` – Speech-to-text + audio mute intervals

Folder: [`src/aegisai/audio`](./audio)

Responsibilities:

* Convert media to **16 kHz mono LINEAR16 WAV** for STT.
* Call **Google Speech-to-Text** and normalize the output.
* Detect bad words + build **time intervals** to mute.
* Provide:

  * **File-based** audio filtering: `filter_audio_file(...)`
  * **Streaming** audio filter skeleton: `AudioStreamFilter`
  * Chunk workers (`audio_worker`) and a rolling **TextBuffer** for context.

Outputs:

* `List[Interval] = list[(start_sec, end_sec)]` on the original audio timeline.
* Optional muted audio file (file mode only).

Used by:

* `pipeline.file_runner` for file jobs.
* `pipeline.stream_runner.StreamModerationPipeline` (via `AudioStreamFilter`).

---

### 2. `moderation` – Shared text / transcript rules

Folder: [`src/aegisai/moderation`](./moderation)

Responsibilities:

* Central **profanity vocabulary** (`BAD_WORDS`) with normalization helpers.
* Text analysis rules:

  * `analyze_text` / `analyze_transcript` → `TextModerationResult`
  * Severity bucketing (0–3) based on count of bad words.
  * Local `block` flag (severity ≥ 2).
* Policy hook:

  * `should_block_text(result, mode="default")`
    Currently **stricter** than text rules (`count > 0` → block).

Used by:

* `audio.workers.audio_worker` to decide if a chunk should be muted / reported.
* Any future **text-only** moderation endpoints.

---

### 3. `vision` – Google Vision wrappers + frame-level decisions

Folder: [`src/aegisai/vision`](./vision)

Responsibilities:

* Wrap **Google Cloud Vision**:

  * **SafeSearch** → nudity / racy / violence flags.
  * **Label detection** → violence-related labels.
  * **Object localization** → pixel bounding boxes for persons, weapons, etc.
* Convert raw Vision output to:

  * `FrameModerationResult(timestamp, safesearch, labels, block)`
  * Continuous unsafe time intervals (via `intervals_from_frames`).
* Violence dictionary:

  * `VIOLENCE_LABELS` – curated label list for guns, gore, war, etc.

Used by:

* `video.filter_file` and `video.filter_stream` to mark unsafe frames.
* `video.region_blur` for object-level blur boxes.

> Requires `GOOGLE_APPLICATION_CREDENTIALS` pointing to a service account with Vision access.

---

### 4. `video` – Video moderation, blur & reconstruction

Folder: [`src/aegisai/video`](./video)

Responsibilities:

* **Frame sampling** (1–3 FPS) for efficient moderation.
* Call Vision-based `analyze_frame_moderation`.
* Turn per-frame decisions into:

  * Unsafe **intervals**
  * Per-frame **object bounding boxes**
* Apply censoring:

  * Full-frame blur / mute via FFmpeg (`ffmpeg_edit.py`)
  * Object-level blur with original audio preserved (`region_blur.py`)
* Support both:

  * **File-based** filtering (`filter_video_file(...)`)
  * **Streaming** filtering (`VideoStreamFilter`, chunk-based)

Key pieces:

* `filter_file.filter_video_file` – sample frames, run moderation, return:

  ```python
  {
    "intervals": [...],
    "object_boxes": [...],
    "sample_fps": 1.0,
  }
  ```
* `ffmpeg_edit.blur_and_mute_intervals_in_video` – one-pass FFmpeg blur + mute.
* `region_blur.blur_moving_objects_with_intervals` – blur only detected objects inside unsafe intervals.
* `segment.extract_audio_chunks_from_video` – shared audio extraction for STT side.
* `live_buffer.LiveFrameBuffer` – rolling buffer for 5–10s streaming delay.

---

### 5. `pipeline` – Orchestration & public API

Folder: [`src/aegisai/pipeline`](./pipeline)

Responsibilities:

* Define **what job to run** and **which modules to call**.
* Provide high-level APIs for both **files** and **streams**.
* Expose **8 named presets** for common scenarios.

Core pieces:

* `PipelineConfig` (in `config.py`):

  ```python
  PipelineConfig(
      media_type="audio" | "video",
      mode="file" | "stream",
      filter_audio: bool,
      filter_video: bool,
      # optional extras like audio_chunk_seconds, sample_fps, workers, ...
  )
  ```

* File pipeline (`file_runner.py`):

  * `run_file_job(cfg, input_path, output_path) -> dict`
  * Handles:

    1. Audio files → muted audio.
    2. Video files, audio-only → mute audio in video.
    3. Video files, video-only → blur video (full-frame or object-level), keep audio.
    4. Video files, audio+video → blur + mute.

* Streaming pipeline (`stream_runner.py`):

  * `StreamModerationPipeline(output_dir, ...)`
  * Accepts `ChunkDescriptor` objects (chunked MP4 + audio path).
  * Runs audio + video analysis in parallel.
  * Emits `FilteredChunk`s with censored MP4s.

* Presets (`use_cases.py`):

  1. `AUDIO_FILE_FILTER`
  2. `AUDIO_STREAM_FILTER`
  3. `VIDEO_FILE_AUDIO_ONLY`
  4. `VIDEO_FILE_VIDEO_ONLY`
  5. `VIDEO_FILE_AUDIO_VIDEO`
  6. `VIDEO_STREAM_AUDIO_ONLY`
  7. `VIDEO_STREAM_VIDEO_ONLY`
  8. `VIDEO_STREAM_AUDIO_VIDEO`

These configs allow external code (backend / CLI) to call the engine without worrying about the wiring.

---

## Quick start (file mode)

Minimal example for a **video file → blur + mute**:

```python
from pathlib import Path
from aegisai.pipeline.config import PipelineConfig
from aegisai.pipeline.file_runner import run_file_job
from aegisai.pipeline.use_cases import VIDEO_FILE_AUDIO_VIDEO

cfg = VIDEO_FILE_AUDIO_VIDEO  # PipelineConfig preset

input_path = "input_video.mp4"
output_path = "output_video_filtered.mp4"

result = run_file_job(cfg, input_path, output_path)

print("Output:", result["output_path"])
print("Audio intervals:", result["audio_intervals"])
print("Video intervals:", result["video_intervals"])
```

For an **audio-only file**:

```python
from aegisai.pipeline.use_cases import AUDIO_FILE_FILTER
from aegisai.pipeline.file_runner import run_file_job

cfg = AUDIO_FILE_FILTER
run_file_job(cfg, "input_audio.mp3", "output_audio_filtered.mp3")
```

---

## Quick start (streaming mode)

High-level pattern (details depend on your streaming backend):

```python
from aegisai.pipeline.config import PipelineConfig
from aegisai.pipeline.stream_runner import create_stream_pipeline, ChunkDescriptor

cfg = PipelineConfig(
    media_type="video",
    mode="stream",
    filter_audio=True,
    filter_video=True,
)

pipeline = create_stream_pipeline(cfg, output_dir="filtered_chunks")

# For each incoming chunk from your streaming stack:
desc = ChunkDescriptor(
    chunk_id=0,
    start_ts=0.0,
    duration=5.0,
    video_path="chunk_000.mp4",
    audio_path="chunk_000_audio.wav",
)
pipeline.submit_chunk(desc)

# Periodically poll:
pipeline.poll()
chunk = pipeline.get_ready_chunk_nowait()
if chunk:
    print("Filtered chunk ready:", chunk.output_path)
```

---

## Requirements

* Python 3.10+ (recommended)
* FFmpeg on `PATH`
* Google Cloud:

  * Speech-to-Text API enabled
  * Vision API enabled
  * `GOOGLE_APPLICATION_CREDENTIALS` pointing to a service account JSON

---
