from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.vision.safe_search import analyze_safesearch
from src.aegisai.vision.label_detection import analyze_labels
from src.aegisai.vision.vision_rules import classify_labels, classify_safesearch
from src.aegisai.moderation.text_rules import analyze_transcript
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
#     "data/samples/test_video.mp4",   
#     chunk_seconds=5,
#     text_window_seconds=30,
#     output_video_path="data/samples/test_video_output.mp4",
# )

# input_audio = "data/samples/test_video.mp4"          # your input audio file
# output_audio = "data/samples/test_video_output.mp4"  # where to save filtered result

# result = run_job(
#     cfg=VIDEO_FILE_AUDIO_ONLY,
#     input_path_or_stream=input_audio,
#     output_path=output_audio
# )

# print("Job completed.")
# print(result)


from src.aegisai.pipeline.file_runner import run_job
from src.aegisai.pipeline.use_cases import VIDEO_FILE_AUDIO_VIDEO

input_video = "data/samples/both.mp4"
output_video = "data/samples/both_output.mp4"

result = run_job(
    cfg=VIDEO_FILE_AUDIO_VIDEO,
    input_path_or_stream=input_video,
    output_path=output_video,
)

print("Job completed.")
print(result)

# # ----------------------------
# # STREAMING CODE (COMMENTED OUT)
# # ----------------------------
# import os
# import time
# from src.aegisai.pipeline.stream_runner import (
#     StreamModerationPipeline,
#     ChunkDescriptor,
# )

# # ----------------------------
# # CONFIG
# # ----------------------------
# CHUNKS_DIR = "data/samples/stream_chunks"
# OUTPUT_DIR = "data/samples/stream_chunks_output"

# CHUNK_DURATION = 1.0  # 1-second chunks


# def extract_idx(filename: str) -> int:
#     """
#     'both0.mp4'   -> 0
#     'both5.mp4'   -> 5
#     'both112.mp4' -> 112
#     """
#     name, _ = os.path.splitext(filename)
#     # remove 'both' prefix
#     num_str = name.replace("both", "")
#     return int(num_str)


# # ----------------------------
# # SETUP PIPELINE
# # ----------------------------
# pipeline = StreamModerationPipeline(
#     output_dir=OUTPUT_DIR,
#     audio_workers=8,
#     video_workers=12,
#     sample_fps=1.0,
#     ffmpeg_workers=2,
# )

# print("🔧 Pipeline initialized.")

# # ----------------------------
# # GET ALL CHUNK FILES (NUMERIC ORDER)
# # ----------------------------
# all_files = [
#     f for f in os.listdir(CHUNKS_DIR)
#     if f.startswith("both") and f.endswith(".mp4")
# ]

# files = sorted(all_files, key=extract_idx)

# print(f"Found {len(files)} chunks.")


# # ----------------------------
# # MAIN STREAM LOOP
# # ----------------------------
# for filename in files:
#     idx = extract_idx(filename)  # true chunk index from original video
#     chunk_path = os.path.join(CHUNKS_DIR, filename)

#     desc = ChunkDescriptor(
#         chunk_id=idx,
#         start_ts=float(idx),      # second idx in original video
#         duration=CHUNK_DURATION,
#         video_path=chunk_path,
#         audio_path=chunk_path,
#     )

#     print(f"➡️  Sending chunk {idx}: {filename}")
#     pipeline.submit_chunk(desc)

#     # simulate 1 second streaming delay
#     time.sleep(1)

#     # poll for ready chunks
#     pipeline.poll()

#     # fetch all ready chunks
#     while True:
#         ready = pipeline.get_ready_chunk_nowait()
#         if ready is None:
#             break
#         print(f"✅ Ready chunk {ready.chunk_id} → {ready.output_path}")


# # ----------------------------
# # CLOSE PIPELINE (end of stream)
# # ----------------------------
# print("\nStream ended. Finalizing…")
# pipeline.close()

# # Drain remaining
# while True:
#     ready = pipeline.get_ready_chunk_nowait()
#     if ready is None:
#         break
#     print(f"🟢 Final ready chunk {ready.chunk_id} → {ready.output_path}")

# print("\n🎉 Done! All chunks processed.")
