import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from google.cloud import vision

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aegisai.vision.safe_search import (
    GoogleSafeSearchClient,
    SafeSearchCategoryScores,
    SafeSearchError,
    SafeSearchLikelihood,
)


def _build_response(
    *,
    adult: int = SafeSearchLikelihood.POSSIBLE,
    spoof: int = SafeSearchLikelihood.VERY_UNLIKELY,
    medical: int = SafeSearchLikelihood.UNLIKELY,
    violence: int = SafeSearchLikelihood.LIKELY,
    racy: int = SafeSearchLikelihood.UNLIKELY,
    error_message: str = "",
):
    annotation = type(
        "SafeSearchAnnotation",
        (),
        {
            "adult": adult,
            "spoof": spoof,
            "medical": medical,
            "violence": violence,
            "racy": racy,
        },
    )()
    error = type("Error", (), {"message": error_message})()
    return type(
        "Response",
        (),
        {
            "safe_search_annotation": annotation,
            "error": error,
        },
    )()


class SafeSearchClientTests(unittest.TestCase):
    def test_analyze_with_bytes(self) -> None:
        client = MagicMock()
        client.safe_search_detection.return_value = _build_response()

        service = GoogleSafeSearchClient(client=client)
        result = service.analyze(image_bytes=b"\xff\xd8\xff")

        self.assertEqual(result.adult, SafeSearchLikelihood.POSSIBLE)
        called_image = client.safe_search_detection.call_args.kwargs["image"]
        self.assertIsInstance(called_image, vision.Image)
        self.assertEqual(called_image.content, b"\xff\xd8\xff")

    def test_analyze_with_uri(self) -> None:
        client = MagicMock()
        client.safe_search_detection.return_value = _build_response()
        service = GoogleSafeSearchClient(client=client)

        result = service.analyze(image_uri="gs://bucket/frame.png")

        self.assertEqual(result.violence, SafeSearchLikelihood.LIKELY)
        called_image = client.safe_search_detection.call_args.kwargs["image"]
        self.assertIsInstance(called_image, vision.Image)
        self.assertEqual(called_image.source.image_uri, "gs://bucket/frame.png")

    def test_analyze_raises_on_error(self) -> None:
        client = MagicMock()
        client.safe_search_detection.return_value = _build_response(
            error_message="auth failed"
        )
        service = GoogleSafeSearchClient(client=client)

        with self.assertRaises(SafeSearchError):
            service.analyze(image_bytes=b"\x00\x01")

    def test_scores_threshold_check(self) -> None:
        scores = SafeSearchCategoryScores(
            adult=SafeSearchLikelihood.UNKNOWN,
            spoof=SafeSearchLikelihood.VERY_UNLIKELY,
            medical=SafeSearchLikelihood.UNLIKELY,
            violence=SafeSearchLikelihood.LIKELY,
            racy=SafeSearchLikelihood.POSSIBLE,
        )
        self.assertTrue(
            scores.exceeds(
                minimum=SafeSearchLikelihood.POSSIBLE, categories=["violence", "adult"]
            )
        )
        self.assertFalse(scores.exceeds(minimum=SafeSearchLikelihood.VERY_LIKELY))


if __name__ == "__main__":
    unittest.main()


