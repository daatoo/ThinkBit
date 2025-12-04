import queue
from typing import List

from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.audio.intervals import detect_toxic_segments
from src.aegisai.audio.text_buffer import TextBuffer
from src.aegisai.moderation.text_rules import analyze_text, TextModerationResult

def audio_worker(
    audio_q: "queue.Queue",
    event_q: "queue.Queue",
    text_buffer: TextBuffer,
    muted_intervals: list[tuple[float, float]],
    chunk_seconds: int,
) -> None:
    """
    Worker that processes audio chunks.

    audio_q items: (wav_path: str, timestamp_start: float)
    For each chunk:
      - transcribe_audio(wav_path)
      - append to TextBuffer
      - analyze_text(window_text)
      - if result.block: put event into event_q
    """
    while True:
        item = audio_q.get()
        if item is None:
            # stop signal
            print("[audio_worker] Stop signal received")
            audio_q.task_done()
            break

        wav_path, ts = item
        print(f"[audio_worker] Processing chunk at t={ts:.1f}s -> {wav_path}")

        try:
            raw = transcribe_audio(wav_path)
        except Exception as e:
            print(f"[audio_worker] Error in transcribe_audio({wav_path}): {e}")
            audio_q.task_done()
            continue

        # =========================
        #  Normalize STT result
        # =========================
        transcripts: list[str]
        words: list[dict]



        if isinstance(raw, dict):
            transcripts = raw.get("transcripts", [])
            words = raw.get("words", [])
        elif isinstance(raw, list):
            # backward compatibility: old version returned list of strings
            transcripts = [str(x) for x in raw]
            words = []
        else:
            transcripts = [str(raw)]
            words = []

        text = " ".join(transcripts)
        print(f"[audio_worker] Transcript (t={ts:.1f}s): {text[:120]!r}")

        if text.strip():
            # Update rolling window
            text_buffer.add(ts, text)

            try:
                result: TextModerationResult = analyze_text(text)
            except Exception as e:
                print(f"[audio_worker] Error in analyze_text: {e}")
                result = TextModerationResult(
                    original_text=text,
                    bad_words=[],
                    count=0,
                    severity=0,
                    block=False,
                )

            print(
                f"[audio_worker] Moderation: count={result.count}, "
                f"severity={result.severity}, block={result.block}, "
                f"bad_words={result.bad_words}"
            )

            if result.block:
                # Emit a moderation event
                event_q.put({
                    "source": "audio",
                    "timestamp": ts,
                    "bad_words": result.bad_words,
                    "count": result.count,
                    "severity": result.severity,
                    "text_window": result.original_text,
                })



        # =========================
        #  Word-level mute intervals
        # =========================
        if words:
            # local segments: relative to this chunk (0..chunk_seconds)
            local_segments = detect_toxic_segments(words)
            if local_segments:
                print(f"[audio_worker] Toxic word segments (local): {local_segments}")

            # Convert to global timeline by adding chunk start time `ts`
            for start_local, end_local in local_segments:
                start_global = ts + start_local
                end_global = ts + end_local
                muted_intervals.append((start_global, end_global))

        else:
            # Fallback: if no word timestamps but we decided to block,
            # mute whole chunk like old behavior.
            if text.strip():
                try:
                    if result.block:
                        muted_intervals.append((ts, ts + chunk_seconds))
                except NameError:
                    # if analyze_text failed entirely
                    pass

        audio_q.task_done()