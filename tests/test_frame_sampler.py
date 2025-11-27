import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aegisai.video_processing.frame_sampler import FrameSampler, SamplingPlan


class FrameSamplerTests(unittest.TestCase):
    def test_plan_clamps_to_range(self) -> None:
        sampler = FrameSampler()
        plan = sampler.plan(60.0)
        self.assertIsInstance(plan, SamplingPlan)
        self.assertGreater(plan.stride, 1)
        self.assertTrue(1 <= plan.target_fps <= 3)

    def test_should_emit_every_stride(self) -> None:
        sampler = FrameSampler()
        plan = sampler.plan(30.0)
        emitted = [i for i in range(30) if sampler.should_emit(i, plan)]
        self.assertTrue(all(idx % plan.stride == 0 for idx in emitted))

    def test_default_when_source_unknown(self) -> None:
        sampler = FrameSampler()
        plan = sampler.plan(None)
        self.assertEqual(plan.source_fps, sampler.default_fps)
        self.assertEqual(plan.stride, 1)


if __name__ == "__main__":
    unittest.main()


