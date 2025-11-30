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


def analyze_safesearch(image_path: str, key_path: str = "secrets/aegis-key.json") -> SafeSearchResult:
    client = vision.ImageAnnotatorClient.from_service_account_file(key_path)

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
