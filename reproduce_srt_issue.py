
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.aegisai.audio.filter_file import filter_audio_file
from src.aegisai.moderation.bad_words_list import BAD_WORDS

def test_srt_parsing():
    # Create a dummy SRT file
    srt_content = """1
00:00:01,000 --> 00:00:02,000
This is a test.

2
00:00:02,500 --> 00:00:03,500
fuck this.
"""
    srt_path = "test.srt"
    with open(srt_path, "w") as f:
        f.write(srt_content)

    # Create a dummy audio file (needed for the function signature, even if not used when subtitle_path is present)
    # Actually filter_audio_file checks if audio_path exists.
    audio_path = "test_audio.wav"
    with open(audio_path, "w") as f:
        f.write("dummy audio content")

    print(f"Testing with SRT containing: 'fuck this.'")
    
    try:
        intervals = filter_audio_file(audio_path, subtitle_path=srt_path)
        print(f"Intervals found: {intervals}")
        
        if intervals:
            print("SUCCESS: Bad word was detected.")
        else:
            print("FAILURE: Bad word was NOT detected.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(srt_path):
            os.remove(srt_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    test_srt_parsing()
