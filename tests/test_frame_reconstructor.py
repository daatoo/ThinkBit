import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aegisai.video_processing.frame_reconstructor import (
    CensorEffectType,
    CensorInstruction,
    FrameReconstructionPipeline,
)


class FrameReconstructorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = FrameReconstructionPipeline(ffmpeg_path="ffmpeg")

    def test_black_box_effect(self) -> None:
        img = Image.new("RGB", (20, 20), (255, 255, 255))
        instr = CensorInstruction(
            effect_type=CensorEffectType.BLACK_BOX,
            start_time=0.0,
            end_time=1.0,
            x=5,
            y=5,
            width=10,
            height=10,
            color=(0, 0, 0),
        )
        result = self.pipeline.apply_effects(img, [instr])
        pixel = result.getpixel((10, 10))
        self.assertEqual(pixel, (0, 0, 0))

    def test_pixelate_effect_changes_region(self) -> None:
        img = Image.new("RGB", (20, 20), (0, 255, 0))
        for x in range(5, 15):
            img.putpixel((x, 10), (255, 0, 0))
        instr = CensorInstruction(
            effect_type=CensorEffectType.PIXELATE,
            start_time=0.0,
            end_time=1.0,
            x=5,
            y=5,
            width=10,
            height=10,
            intensity=5,
        )
        result = self.pipeline.apply_effects(img, [instr])
        self.assertNotEqual(result.getpixel((10, 10)), (255, 0, 0))

    def test_blur_effect_softens_region(self) -> None:
        img = Image.new("RGB", (20, 20), (0, 0, 255))
        img.putpixel((10, 10), (255, 255, 255))
        instr = CensorInstruction(
            effect_type=CensorEffectType.BLUR,
            start_time=0.0,
            end_time=1.0,
            x=8,
            y=8,
            width=4,
            height=4,
            intensity=2,
        )
        result = self.pipeline.apply_effects(img, [instr])
        self.assertNotEqual(result.getpixel((10, 10)), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()


