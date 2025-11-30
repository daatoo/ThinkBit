# Aegis AI — Core Moderation Engine

This directory contains the core implementation of **Aegis**, a modular
audio–video moderation pipeline designed to process streaming or offline
content with low latency (≤5 seconds). The system combines:

- **Speech-to-text transcription**
- **Text moderation rules**
- **Frame extraction & sampling**
- **Vision API integration**
- **Concurrent audio/video workers**
- **Unified event dispatching**

Aegis is built to scale from offline MP4 processing to real-time
WebRTC/RTMP moderation.

---

# 🔌 Directory Overview


```markdown
aegisai/
│
├── audio/          # Speech-to-text transcription and audio utilities
│
├── video/          # Frame extraction, sampling, reconstruction, and video muting
│
├── vision/         # Google Vision API integration, SafeSearch, label rules
│
├── moderation/     # Text moderation rules, keyword policies, profanity lists
│
└──  pipeline/       # Unified streaming pipeline: audio workers, video workers, decision worker
```


---

# 🧩 Module Summary

## `audio/`
Handles all audio-related logic:

- `speech_to_text.py` — audio transcription (Google STT / Whisper / etc.)
- Utilities for WAV/MP3 handling
- Used by `audio_worker` inside the pipeline

## `moderation/`
Implements text moderation policy:

- `text_rules.py` — rule engine (keywords, block list, severity levels)
- `policy.py` — configuration for filtering behavior
- `bad_words_list.py` — canonical profanity list
- Returns structured `TextModerationResult` objects

## `video/`
Video frame handling, including:

- `ffmpeg_extractor.py` — extract frames from video via FFmpeg
- `frame_sampler.py` — reduce FPS (30 → 1–3 fps) in streaming mode
- `frame_reconstructor.py` — (optional) rebuild video with blurred/muted areas
- `mute.py` — mute audio ranges in a final output video
- `segment.py` — extract audio segments via FFmpeg

## `vision/`
Wrapper around Google Vision:

- `label_detection.py` — label extraction
- `safe_search.py` — NSFW detection
- `vision_rules.py` — rule-based decisions (weapon, nudity, graphic violence)
- `label_lists.py` — Contains canonical lists of labels that Aegis considers dangerous

## `pipeline/`
The heart of Aegis:

- `streaming.py` — unified audio/video pipeline with:
  - audio_worker  
  - video_worker (optional, WIP)  
  - decision_worker  
  - timestamp-based rolling text buffer  
  - interval merging + output muting  
  - offline and streaming modes

This module is responsible for concurrency, queue-based message passing,
and producing actionable moderation events.

---

# 🚀 Quickstart (Offline Audio + Video)

Below is an example of running Aegis on an offline MP4 file:

```python
from src.aegisai.pipeline.streaming import process_file_audio_only

process_file_audio_only(
    video_path="input.mp4",
    chunk_seconds=5,
    text_window_seconds=30,
    output_video_path="output-muted.mp4",
)
```