"""
Frame reconstruction pipeline with region-level censoring effects.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Sequence

from PIL import Image, ImageFilter


class ReconstructionError(RuntimeError):
    """Raised when frame reconstruction fails."""


class CensorEffectType(str, Enum):
    BLUR = "blur"
    PIXELATE = "pixelate"
    BLACK_BOX = "black_box"


@dataclass(frozen=True)
class CensorInstruction:
    """
    Describes a censoring effect applied to a rectangular region.

    Attributes:
        effect_type: blur, pixelate, or black_box.
        start_time: seconds when the effect activates (inclusive).
        end_time: seconds when the effect deactivates (inclusive).
        x/y/width/height: Bounding box in pixels.
        intensity: Effect-dependent strength (blur radius or pixel block size).
        color: RGB tuple for black boxes.
    """

    effect_type: CensorEffectType
    start_time: float
    end_time: float
    x: int
    y: int
    width: int
    height: int
    intensity: float = 12.0
    color: tuple[int, int, int] = (0, 0, 0)

    def active_at(self, timestamp: float) -> bool:
        return self.start_time <= timestamp <= self.end_time


@dataclass
class ReconstructionResult:
    output_path: Path
    frame_count: int
    fps: float
    applied_effects: int


class FrameReconstructionPipeline:
    """
    Applies censoring effects to sampled frames and rebuilds a video via FFmpeg.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg") -> None:
        self.ffmpeg_path = ffmpeg_path

    def _ensure_ffmpeg(self) -> None:
        if shutil.which(self.ffmpeg_path) is None:
            raise ReconstructionError(
                "FFmpeg binary not found. Install FFmpeg and ensure it is on the PATH."
            )

    def reconstruct(
        self,
        frames_dir: Path | str,
        output_path: Path | str,
        fps: float,
        instructions: Sequence[CensorInstruction] | None = None,
        audio_path: Path | str | None = None,
        image_format: str = "jpg",
    ) -> ReconstructionResult:
        """
        Rebuild a video from processed frames and optional audio track.
        """
        self._ensure_ffmpeg()

        if fps <= 0:
            raise ValueError("fps must be positive.")

        instructions = instructions or []
        frames_dir = Path(frames_dir).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()
        if audio_path is not None:
            audio_path = Path(audio_path).expanduser().resolve()

        frame_paths = sorted(frames_dir.glob(f"*.{image_format}"))
        if not frame_paths:
            raise ReconstructionError("No frames found to reconstruct video.")

        with tempfile.TemporaryDirectory(prefix="processed_frames_") as tmpdir:
            processed_dir = Path(tmpdir)
            effect_count = self._process_frames(
                frame_paths, processed_dir, fps, instructions
            )

            frame_pattern = str(processed_dir / f"frame_%06d.{image_format}")
            for idx, frame in enumerate(sorted(processed_dir.glob(f"*.{image_format}"))):
                target_name = processed_dir / f"frame_{idx:06d}.{image_format}"
                if frame != target_name:
                    frame.rename(target_name)

            cmd = [
                self.ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                f"{fps:.3f}",
                "-i",
                frame_pattern,
            ]

            if audio_path:
                cmd.extend(["-i", str(audio_path), "-c:a", "aac", "-shortest"])

            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(output_path),
                ]
            )

            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if process.returncode != 0:
                raise ReconstructionError(
                    f"FFmpeg reconstruction failed: {process.stderr.strip()}"
                )

        return ReconstructionResult(
            output_path=output_path,
            frame_count=len(frame_paths),
            fps=fps,
            applied_effects=effect_count,
        )

    def _process_frames(
        self,
        frame_paths: Sequence[Path],
        processed_dir: Path,
        fps: float,
        instructions: Sequence[CensorInstruction],
    ) -> int:
        processed_dir.mkdir(parents=True, exist_ok=True)
        applied = 0
        for index, frame_path in enumerate(frame_paths):
            with Image.open(frame_path) as img:
                image = img.convert("RGB")
            timestamp = index / fps
            active = [instr for instr in instructions if instr.active_at(timestamp)]
            if active:
                image = self.apply_effects(image, active)
                applied += len(active)

            output_path = processed_dir / frame_path.name
            image.save(output_path, quality=95)
        return applied

    @staticmethod
    def apply_effects(image: Image.Image, instructions: Sequence[CensorInstruction]) -> Image.Image:
        """
        Apply censoring instructions to an image in-place and return it.
        """
        mutable = image.copy()
        for instruction in instructions:
            FrameReconstructionPipeline._apply_effect(mutable, instruction)
        return mutable

    @staticmethod
    def _apply_effect(image: Image.Image, instruction: CensorInstruction) -> None:
        x1 = max(instruction.x, 0)
        y1 = max(instruction.y, 0)
        x2 = min(instruction.x + instruction.width, image.width)
        y2 = min(instruction.y + instruction.height, image.height)
        if x1 >= x2 or y1 >= y2:
            return

        region = image.crop((x1, y1, x2, y2))
        if instruction.effect_type is CensorEffectType.BLUR:
            radius = max(instruction.intensity, 1)
            region = region.filter(ImageFilter.GaussianBlur(radius=radius))
        elif instruction.effect_type is CensorEffectType.PIXELATE:
            block = max(int(instruction.intensity), 2)
            down_w = max(1, (x2 - x1) // block)
            down_h = max(1, (y2 - y1) // block)
            region = region.resize((down_w, down_h), Image.NEAREST)
            region = region.resize((x2 - x1, y2 - y1), Image.NEAREST)
        elif instruction.effect_type is CensorEffectType.BLACK_BOX:
            region = Image.new("RGB", (x2 - x1, y2 - y1), instruction.color)
        else:
            raise ReconstructionError(f"Unsupported effect type: {instruction.effect_type}")

        image.paste(region, (x1, y1))


