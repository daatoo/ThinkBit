import sys
import os
from pathlib import Path

# Add src to path
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from src.aegisai.video.filter_file import filter_video_file

def verify():
    # Use test_video.mp4 if available, else dummy_valid.mp4
    candidates = ["test_video.mp4", "dummy_valid.mp4"]
    input_filename = None
    for c in candidates:
        if (base_dir / "src/backend/uploads" / c).exists():
            input_filename = c
            break
            
    if not input_filename:
        print("No test video found in src/backend/uploads")
        return

    input_path = str(base_dir / "src/backend/uploads" / input_filename)
    output_path = str(base_dir / "src/backend/outputs/verify_output.mp4")
    
    print(f"Processing {input_path}...")
    try:
        result = filter_video_file(
            input_path=input_path,
            output_path=output_path,
            sample_fps=2.0,
            extend_intervals=True
        )
        
        print("\nProcessing Complete!")
        print(f"Intervals found: {result.get('intervals')}")
        print(f"Sample FPS: {result.get('sample_fps')}")
        
        if os.path.exists(output_path):
            print(f"SUCCESS: Output file created at {output_path}")
        else:
            print("FAILURE: Output file not created")
            
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
