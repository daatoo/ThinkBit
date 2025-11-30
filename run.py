from src.aegisai.audio.speech_to_text import transcribe_audio, convert_mp3_to_wav
from src.aegisai.vision.safe_search import analyze_safesearch
from src.aegisai.vision.label_detection import analyze_labels
from src.aegisai.vision.vision_rules import classify_labels, classify_safesearch
from src.aegisai.moderation.text_rules import analyze_transcript
from src.aegisai.pipeline.streaming import process_file_audio_only

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

process_file_audio_only(
    "/home/david/Desktop/ThinkBit/data/samples/test_video.mp4",   
    chunk_seconds=5,
    text_window_seconds=30,
    output_video_path="/home/david/Desktop/ThinkBit/data/samples/test_video_output.mp4",
)






