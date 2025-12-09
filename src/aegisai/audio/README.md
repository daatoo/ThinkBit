# `src/aegisai/audio/` – Audio Module

Audio-side logic for AegisAI:

- Converts input media to STT-friendly WAV.
- Runs Google Speech-to-Text.
- Detects toxic words and builds mute intervals.
- Provides:
  - **File-based** audio moderation (`filter_file.py` + `workers.py`)
  - **Streaming** audio pipeline skeleton (`filter_stream.py`)
  - Interval helpers (`intervals.py`)
  - Shared rolling text window (`text_buffer.py`)

---

## `converters.py`

Simple helper for audio format conversion.

### `convert_mp3_to_wav(input_path: str, output_path: str)`

- Uses `pydub.AudioSegment`.
- Converts MP3 → WAV with:
  - 16 kHz sample rate
  - mono
  - LINEAR16 encoding
- Output is suitable for Google Speech-to-Text.

---

## `speech_to_text.py`

Wrapper around **Google Cloud Speech-to-Text**.

### `_get_client() -> speech.SpeechClient`

- Lazily creates and caches a global `SpeechClient` instance.

### `transcribe_audio(file_path: str) -> dict`

- Input:
  - Path to a **16 kHz mono LINEAR16 WAV** file.
- Config:
  - `language_code="en-US"`
  - `encoding=LINEAR16`
  - `sample_rate_hertz=16000`
  - `enable_word_time_offsets=True`
- Calls `client.recognize(...)` and returns:

```python
{
    "transcripts": [str, ...],  # full text hypotheses
    "words": [
        {
            "word": str,
            "start": float,  # seconds
            "end": float,    # seconds
        },
        ...
    ],
}
````

Used by:

* `audio.workers.audio_worker` (file-based moderation)
* `audio.filter_stream.AudioStreamFilter` (streaming)

---

## `intervals.py`

Helpers for toxic word → time interval logic.

### Types

* `Interval = tuple[float, float]`
  Represents `[start_sec, end_sec]` in seconds.

### `detect_toxic_segments(words: List[dict], padding=0.15, max_gap=0.25) -> List[Interval]`

* Input:

  * `words`: items of `{ "word": str, "start": float, "end": float }`
    (usually from `transcribe_audio(...]["words"]`).
* Uses `is_bad_word(word)` from `moderation.bad_words_list` to detect toxic tokens.
* For each bad word:

  * Builds a segment `[start - padding, end + padding]`.
  * Merges close segments if the gap between them ≤ `max_gap`.
* Output:

  * List of **continuous toxic segments** in **local chunk time** `[0, chunk_seconds]`.

### `merge_intervals(intervals: List[Interval]) -> List[Interval]`

* Sorts intervals by start time.
* Merges overlapping or touching intervals.
* Used to combine global mute intervals after processing all chunks.

---

## `text_buffer.py`

Rolling text window used for moderation context.

### `TextBuffer`

Stores `(timestamp, text)` pairs and keeps only recent entries.

* `__init__(window_seconds: int = 30)`

  * Only keeps text from the last `window_seconds` seconds.
* `add(timestamp: float, text: str) -> None`

  * Adds a new text snippet and cleans up old entries.
* `get_text() -> str`

  * Concatenates all text currently in the buffer window.

Used by:

* `audio.workers.audio_worker` (file-based moderation)
* Optionally by `AudioStreamFilter` for streaming.

---

## `workers.py`

Low-level worker used by file-based audio moderation.

### `audio_worker(audio_q, event_q, text_buffer: TextBuffer, muted_intervals: list[Interval], chunk_seconds: int) -> None`

* **Input queue**: `audio_q`

  * Items: `(wav_path: str, timestamp_start: float)`
  * `None` item signals **stop**.

* **Output queue**: `event_q`

  * Receives moderation events on blocked chunks.

* **Shared state**:

  * `text_buffer`: `TextBuffer` for rolling context.
  * `muted_intervals`: list that is appended with `(start_global, end_global)` intervals.

* Steps per chunk:

  1. `transcribe_audio(wav_path)` → `raw`
  2. Normalize STT output:

     * If dict: `transcripts = raw["transcripts"]`, `words = raw["words"]`
     * Else: fall back to list/string handling
  3. Join transcripts into `text` and:

     * Add `(ts, text)` into `text_buffer`.
     * Call `analyze_text(text)` from `moderation.text_rules`.
     * Log moderation result (`count`, `severity`, `block`, `bad_words`).
     * If `result.block`:

       * Put an event into `event_q`:

         ```python
         {
             "source": "audio",
             "timestamp": ts,
             "bad_words": result.bad_words,
             "count": result.count,
             "severity": result.severity,
             "text_window": result.original_text,
         }
         ```
  4. Word-level muting:

     * If `words` list is available:

       * `local_segments = detect_toxic_segments(words)`
       * Convert to global:

         * `(ts + start_local, ts + end_local)`
           and append to `muted_intervals`.
     * Else (no word timestamps) and `result.block == True`:

       * Fallback: mute the **entire chunk** `[ts, ts + chunk_seconds]`.

* Stops when it reads `None` from `audio_q`.

Used by:

* `audio.filter_file.filter_audio_file` (spawns multiple `audio_worker` threads).

---

## `filter_file.py`

File-based audio moderation entrypoint.

### Internal helper: `_mute_intervals_in_audio_file(audio_path, intervals, output_audio_path)`

* Uses `ffmpeg` to mute selected time ranges in an **audio-only** file.
* If `intervals` is empty:

  * Copies input → `output_audio_path` (no re-encode).
* If non-empty:

  * Builds a chain of `volume` filters:

    ```text
    volume=enable='between(t,start,end)':volume=0
    ```
  * Applies them via `ffmpeg` and re-encodes audio (`-c:a aac`).

### `filter_audio_file(audio_path: str, output_audio_path: str | None = None, chunk_seconds: int = 5) -> List[Interval]`

* Assumes input is an **audio** file (wav/mp3/etc.), not video.

* High-level behavior:

  1. Validates `audio_path` exists.
  2. Creates:

     * `muted_intervals: List[Interval] = []`
     * `text_buffer = TextBuffer()`
     * `audio_q`, `event_q` – worker queues.
  3. Spawns `num_workers = 12` threads running `audio_worker(...)`.
  4. Uses `extract_audio_chunks_from_video` (works for audio-only too) to split the file into chunks of length `chunk_seconds` and enqueue them:

     * Each chunk queued as `(wav_path, ts)` with `ts = idx * chunk_seconds`.
  5. Sends `None` to `audio_q` for each worker and waits for:

     * `audio_q.join()` (all tasks complete).
     * `t.join()` on each worker thread.
  6. Calls `merge_intervals(muted_intervals)` to combine global mute ranges.
  7. If `output_audio_path` is provided:

     * Uses `_mute_intervals_in_audio_file(...)` to create the filtered audio file.
  8. Returns the **merged intervals**.

* **Return value**:

  * `List[Interval]` = list of `(start_sec, end_sec)` on the **original audio timeline**.

Used by:

* `pipeline.file_runner.run_file_job` for:

  * pure audio file pipelines,
  * or audio-only analysis when combined with video.

---

## `filter_stream.py`

Minimal streaming audio pipeline (currently only STT + logging, no muting).

### Types

```python
Interval = tuple[float, float]   # absolute timestamps in stream timeline
```

```python
class AudioJob(NamedTuple):
    chunk_id: int
    audio_path: str
    start_ts: float
    duration: float
```

```python
class AudioResult(NamedTuple):
    chunk_id: int
    intervals: List[Interval]  # ABSOLUTE time; currently always []
```

### `AudioStreamFilter`

High-level interface used by the **streaming pipeline**.

#### `__init__(num_workers: int = 12, text_buffer: Optional[TextBuffer] = None)`

* Initializes:

  * `self.job_q: Queue[AudioJob | None]`
  * `self.result_q: Queue[AudioResult]`
  * `self.text_buffer` (new or provided)
  * `num_workers` worker threads that run `_worker_loop()`.

#### `_worker_loop()`

* Continuously:

  * Gets `AudioJob` from `job_q`.
  * If `job is None` → stop.
  * Otherwise:

    * Calls `_process_job(job)`.
    * Puts non-`None` `AudioResult` into `result_q`.

#### `_process_job(job: AudioJob) -> Optional[AudioResult]`

Per chunk:

1. Logs start time.
2. Creates a temp directory and converts `job.audio_path` into:

   * 16 kHz mono WAV via `ffmpeg`.
3. Calls `transcribe_audio(wav_path)` (STT).
4. Normalizes STT output to list of transcripts → single `text` string.
5. If no speech:

   * Logs and returns `AudioResult(chunk_id, [])`.
6. If there is speech:

   * Logs the text (first 120 chars).
   * Currently **does not** do moderation.
   * Returns:

     ```python
     AudioResult(chunk_id=chunk_id, intervals=[])
     ```

> **Note:** This is a skeleton: when you want muting in streaming mode, you can reuse logic from `audio_worker` here (analyze_text + detect_toxic_segments).

#### Public API

* `submit_chunk(chunk_id, audio_path, start_ts, duration) -> None`

  * Enqueues an `AudioJob`.
  * Raises `RuntimeError` if filter is closed.
* `get_result_nowait() -> Optional[AudioResult]`

  * Non-blocking:

    * Returns an `AudioResult` if available.
    * Returns `None` if queue empty.
* `close() -> None`

  * Marks `_closed = True`.
  * Pushes `None` sentinel to `job_q` `num_workers` times.
  * Joins all worker threads.

Used by:

* `pipeline.stream_runner.StreamModerationPipeline` to get audio intervals per chunk
  (currently always empty).

---

```
```
