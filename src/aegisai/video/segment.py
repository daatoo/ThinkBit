import os
import glob
import subprocess
from typing import List


def extract_audio_chunks_from_video(
    video_path: str,
    output_dir: str,
    chunk_seconds: int,
    prefix: str = "chunk_",
) -> List[str]:
    """
    Use ffmpeg to extract the audio track from `video_path` and
    segment it into fixed-length WAV chunks.

    Returns a sorted list of chunk file paths.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    out_pattern = os.path.join(output_dir, f"{prefix}%05d.wav")

    cmd = [
        "ffmpeg",
        "-y",                 # overwrite without asking
        "-i", video_path,     # input file
        "-vn",                # disable video (audio only)
        "-ac", "1",           # mono
        "-ar", "16000",       # 16 kHz sample rate
        "-f", "segment",      # output format: many segments
        "-segment_time", str(chunk_seconds),
        "-reset_timestamps", "1",
        out_pattern,
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg segmentation failed: {e}") from e

    pattern = os.path.join(output_dir, f"{prefix}*.wav")
    chunk_files: List[str] = sorted(glob.glob(pattern))

    return chunk_files



def extract_audio_track(video_path: str, audio_out_path: str) -> None:
    """
    Extract audio track from a video file into a standalone audio file.

    For STT it's usually convenient to:
    - force mono
    - force 16kHz sample rate
    - use a wav container

    You can tweak this later if needed.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",          # no video
        "-ac", "1",     # mono
        "-ar", "16000", # 16 kHz
        audio_out_path,
    ]
    # Check if video has audio stream first
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        video_path
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
        if not result.stdout.strip():
            # No audio stream, create silent audio
            print("No audio stream found, creating silent audio track.")
            # Get duration of video
            duration_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            duration_res = subprocess.run(duration_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
            duration = duration_res.stdout.strip()

            cmd = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=16000:cl=mono",
                "-t", duration,
                audio_out_path
            ]
    except Exception as e:
        print(f"Error probing video: {e}")

    subprocess.run(cmd, check=True)


def extract_subtitles_from_video(video_path: str, output_path: str) -> bool:
    """
    Extract the first available subtitle stream from `video_path` to `output_path`.
    Returns True if successful and file size > 0, False otherwise.
    """
    if not os.path.isfile(video_path):
        return False

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-map", "0:s:0", # Map first subtitle stream
        output_path
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except subprocess.CalledProcessError:
        pass
    
    return False