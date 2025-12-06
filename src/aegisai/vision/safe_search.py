"""
Google SafeSearch client wrapper.
"""

from dataclasses import dataclass
from enum import IntEnum
from google.cloud import vision


class Likelihood(IntEnum):
    UNKNOWN = 0
    VERY_UNLIKELY = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    VERY_LIKELY = 5


@dataclass
class SafeSearchResult:
    adult: Likelihood
    violence: Likelihood
    racy: Likelihood
    medical: Likelihood
    spoof: Likelihood


def analyze_safesearch(image_path: str) -> SafeSearchResult:
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.safe_search_detection(image=image)

    safe = response.safe_search_annotation

    return SafeSearchResult(
        adult=Likelihood(safe.adult),
        violence=Likelihood(safe.violence),
        racy=Likelihood(safe.racy),
        medical=Likelihood(safe.medical),
        spoof=Likelihood(safe.spoof),
    )


from src.aegisai.vision.label_detection import analyze_labels
from src.aegisai.vision.vision_rules import (
    classify_safesearch,
    classify_labels,
    combine_frame_decision,
    FrameModerationResult,
)


def analyze_frame_moderation(
    image_path: str,
    timestamp: float,
) -> FrameModerationResult:
    """
    Full per-frame moderation:
      - SafeSearch
      - label detection
      - classification + final block decision
    """
    # 1) SafeSearch
    ss_result = analyze_safesearch(image_path)
    ss_info = classify_safesearch(ss_result)
    #print(f"[analyze_frame_moderation] SafeSearch info: {ss_info} for {image_path}")

    # 2) Labels (violence etc.)
    labels = analyze_labels(image_path)
    labels_info = classify_labels(labels)
    #print(f"Labels: {labels}")
    #print(f"[analyze_frame_moderation] Labels info: {labels_info} for {image_path}")

    # 3) Combine into one frame-level decision
    return combine_frame_decision(timestamp, ss_info, labels_info)