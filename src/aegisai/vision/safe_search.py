"""
Google Cloud Vision SafeSearch helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Iterable, Tuple

from google.cloud import vision


class SafeSearchError(RuntimeError):
    """Raised when SafeSearch analysis fails or returns an error."""


class SafeSearchLikelihood(IntEnum):
    """Local copy of Vision likelihood values for stable comparisons."""

    UNKNOWN = 0
    VERY_UNLIKELY = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    VERY_LIKELY = 5


@dataclass(frozen=True)
class SafeSearchCategoryScores:
    """
    Stores likelihood scores for each SafeSearch category.
    """

    adult: SafeSearchLikelihood
    spoof: SafeSearchLikelihood
    medical: SafeSearchLikelihood
    violence: SafeSearchLikelihood
    racy: SafeSearchLikelihood

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize scores to a lowercase string map for API consumers.
        """
        return {name: likelihood.name.lower() for name, likelihood in self._iter_scores()}

    def exceeds(
        self,
        *,
        minimum: SafeSearchLikelihood,
        categories: Iterable[str] | None = None,
    ) -> bool:
        """
        Return True if any category in `categories` meets/exceeds `minimum`.
        """
        target_categories = set(categories) if categories else None
        for name, likelihood in self._iter_scores():
            if target_categories and name not in target_categories:
                continue
            if likelihood >= minimum:
                return True
        return False

    def highest_risk(self) -> Tuple[str, SafeSearchLikelihood]:
        """
        Return the category with the highest likelihood value.
        """
        return max(self._iter_scores(), key=lambda item: item[1])

    def _iter_scores(self):
        yield "adult", self.adult
        yield "spoof", self.spoof
        yield "medical", self.medical
        yield "violence", self.violence
        yield "racy", self.racy


class GoogleSafeSearchClient:
    """
    Thin wrapper around Google Cloud Vision SafeSearch detection.
    """

    def __init__(self, client: vision.ImageAnnotatorClient | None = None) -> None:
        self._client = client or vision.ImageAnnotatorClient()

    def analyze(
        self,
        *,
        image_bytes: bytes | None = None,
        image_uri: str | None = None,
    ) -> SafeSearchCategoryScores:
        """
        Run SafeSearch detection on byte content or remotely hosted image.
        """
        if (image_bytes is None and image_uri is None) or (
            image_bytes is not None and image_uri is not None
        ):
            raise ValueError("Provide exactly one of image_bytes or image_uri.")

        image = (
            vision.Image(content=image_bytes)
            if image_bytes is not None
            else vision.Image(source=vision.ImageSource(image_uri=image_uri))
        )

        response = self._client.safe_search_detection(image=image)
        error_message = getattr(getattr(response, "error", None), "message", "") or ""
        if error_message:
            raise SafeSearchError(error_message)

        annotation = getattr(response, "safe_search_annotation", None)
        if annotation is None:
            raise SafeSearchError("SafeSearch annotation missing in response.")

        return SafeSearchCategoryScores(
            adult=self._to_likelihood(annotation.adult),
            spoof=self._to_likelihood(annotation.spoof),
            medical=self._to_likelihood(annotation.medical),
            violence=self._to_likelihood(annotation.violence),
            racy=self._to_likelihood(annotation.racy),
        )

    @staticmethod
    def _to_likelihood(value: int | None) -> SafeSearchLikelihood:
        try:
            return SafeSearchLikelihood(value or 0)
        except ValueError as exc:
            raise SafeSearchError(f"Unexpected likelihood value: {value}") from exc


__all__ = [
    "GoogleSafeSearchClient",
    "SafeSearchCategoryScores",
    "SafeSearchError",
    "SafeSearchLikelihood",
]


