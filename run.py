from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.vision.safe_search import analyze_safesearch
from src.aegisai.vision.label_detection import analyze_labels
from src.aegisai.vision.vision_rules import classify_labels, classify_safesearch
from src.aegisai.moderation.text_rules import analyze_transcript
from src.aegisai.pipeline.streaming import process_file_audio_only

from src.aegisai.pipeline.runner import run_job
from src.aegisai.pipeline.use_cases import AUDIO_FILE_FILTER, VIDEO_FILE_AUDIO_ONLY, VIDEO_FILE_VIDEO_ONLY, VIDEO_FILE_AUDIO_VIDEO

# # ---------- TEST AUDIO ----------
# print("TESTING AUDIO...")
# text = transcribe_audio("data/samples/test.wav")
# print("Transcription:", text)


# # ---------- TEST TEXT MODERATION RULES ----------
# print("TESTING TEXT MODERATION RULES...")
# text_evaluation = analyze_transcript(text)
# print("Text Evaluation:", text_evaluation)


# # ---------- TEST IMAGE SAFE_SEARCH ----------
# print("TESTING IMAGE SAFE_SEARCH...")
# safe_search_results = analyze_safesearch("data/samples/test_image.png")
# print("Safe Search Results:", safe_search_results)

# # ---------- TEST IMAGE LABEL DETECTION ----------
# print("TESTING IMAGE LABEL DETECTION...")
# label_results = analyze_labels("data/samples/test_image.png")
# print("Label Detection Results:", label_results)

# # ---------- TEST VISION RULES ----------
# print("TESTING VISION RULES...")
# vision_evaluation = classify_labels(label_results)
# safe_search_evaluation = classify_safesearch(safe_search_results)
# print("Safe Search Evaluation:", safe_search_evaluation)
# print("Vision Evaluation:", vision_evaluation)

# process_file_audio_only(
#     "/home/david/Desktop/ThinkBit/data/samples/test_video.mp4",   
#     chunk_seconds=5,
#     text_window_seconds=30,
#     output_video_path="/home/david/Desktop/ThinkBit/data/samples/test_video_output.mp4",
# )

# input_audio = "/home/david/Desktop/ThinkBit/data/samples/test_video.mp4"          # your input audio file
# output_audio = "/home/david/Desktop/ThinkBit/data/samples/test_video_output.mp4"  # where to save filtered result

# result = run_job(
#     cfg=VIDEO_FILE_AUDIO_ONLY,
#     input_path_or_stream=input_audio,
#     output_path=output_audio
# )

# print("Job completed.")
# print(result)


# from src.aegisai.pipeline.runner import run_job
# from src.aegisai.pipeline.use_cases import VIDEO_FILE_AUDIO_VIDEO

# input_video = "/home/david/Desktop/ThinkBit/data/samples/both.mp4"
# output_video = "/home/david/Desktop/ThinkBit/data/samples/both_output.mp4"

# result = run_job(
#     cfg=VIDEO_FILE_AUDIO_VIDEO,
#     input_path_or_stream=input_video,
#     output_path=output_video,
# )

# print("Job completed.")
# print(result)
import time
import os

from src.aegisai.pipeline.runner import (
    StreamModerationPipeline,
    ChunkDescriptor,
)

PROGRAM_START = time.time()

def log(*args):
    print(f"[{time.time() - PROGRAM_START:6.3f}s]", *args)


def test_repeated_stream_chunks():
    CHUNK_SECONDS = 1.0
    NUM_CHUNKS = 5               # send 5 chunks for testing
    SEND_INTERVAL = 1.0          # send a chunk every 1 second

    input_chunk = "/home/david/Desktop/ThinkBit/data/samples/output_first1s.mp4"
    output_dir = "/home/david/Desktop/ThinkBit/data/samples/output_first1s_output_dir"

    if not os.path.exists(input_chunk):
        print("ERROR: input chunk does not exist:", input_chunk)
        return

    pipeline = StreamModerationPipeline(
        output_dir=output_dir,
        audio_workers=4,
        video_workers=4,
        sample_fps=1.0,
    )

    log("=== STARTING STREAM TEST ===")

    next_send = time.time()

    for chunk_id in range(NUM_CHUNKS):
        # Wait until the next send time
        now = time.time()
        if now < next_send:
            time.sleep(next_send - now)

        # Describe this chunk
        desc = ChunkDescriptor(
            chunk_id=chunk_id,
            start_ts=chunk_id * CHUNK_SECONDS,
            duration=CHUNK_SECONDS,
            video_path=input_chunk,
            audio_path=input_chunk,
        )

        log(f"Submitting chunk {chunk_id}")
        pipeline.submit_chunk(desc)

        next_send += SEND_INTERVAL

        # Poll results continuously
        pipeline.poll()
        fc = pipeline.get_ready_chunk_nowait()
        if fc is not None:
            log(f"[READY] chunk_id={fc.chunk_id}, output={fc.output_path}")

    log("=== ALL CHUNKS SENT ===")

    # Wait some extra time for late results
    end_wait = time.time() + 3
    while time.time() < end_wait:
        pipeline.poll()
        fc = pipeline.get_ready_chunk_nowait()
        if fc is not None:
            log(f"[READY-LATE] chunk_id={fc.chunk_id}, output={fc.output_path}")
        time.sleep(0.2)

    # Shutdown
    pipeline.close()
    pipeline.poll()

    log("=== STREAM TEST COMPLETE ===")


if __name__ == "__main__":
    test_repeated_stream_chunks()
