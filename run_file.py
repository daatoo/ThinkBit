
from src.aegisai.vision.safe_search import analyze_safesearch
from src.aegisai.vision.label_detection import analyze_labels
from src.aegisai.audio.speech_to_text import transcribe_audio
from src.aegisai.vision.object_localization import localize_objects_from_path
from src.aegisai.video.filter_file import filter_video_file

# # ---------- TEST AUDIO ----------
# print("TESTING AUDIO...")
# text = transcribe_audio("data/samples/test.wav")
# print("Transcription:", text)

# ---------- TEST IMAGE SAFE_SEARCH ----------
# print("TESTING IMAGE SAFE_SEARCH...")
# safe_search_results = analyze_safesearch("data/samples/image.png")
# print("Safe Search Results:", safe_search_results)

# # ---------- TEST IMAGE LABEL DETECTION ----------
# print("TESTING IMAGE LABEL DETECTION...")
# label_results = analyze_labels("data/samples/image.png")
# print("Label Detection Results:", label_results)

# from src.aegisai.vision.object_localization import localize_objects_from_path
# from src.aegisai.video.region_blur import blur_regions_in_single_frame

# frame = "data/samples/image.png"

# objs = localize_objects_from_path(frame)
# print("Localized objects:", objs)
# boxes = [obj.bbox for obj in objs if obj.name.lower() in ("person", "people")]

# blur_regions_in_single_frame(
#     image_path=frame,
#     boxes=boxes,
#     output_path="data/samples/image_blurred.png",
#     blur_radius=18,
# )

# video_result = filter_video_file("data/samples/both.mp4", output_path=None)
# print("Video result:", video_result)

from src.aegisai.pipeline.use_cases import VIDEO_FILE_VIDEO_ONLY
from src.aegisai.pipeline.file_runner import run_job
result = run_job(
    cfg=VIDEO_FILE_VIDEO_ONLY,
    input_path_or_stream="data/samples/both.mp4",
    output_path="data/samples/out_both.mp4"
)


