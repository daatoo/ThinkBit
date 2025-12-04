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
    subprocess.run(cmd, check=True)