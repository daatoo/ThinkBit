"""
Text moderation rules: bad words / profanity detection.
"""

from dataclasses import dataclass
from typing import List
from .bad_words_list import BAD_WORDS  
import re

from .bad_words_list import find_bad_words_in_text


@dataclass
class TextModerationResult:
    original_text: str
    bad_words: List[str]
    count: int
    severity: int
    block: bool


def _compute_severity(count: int) -> int:
    """
    Very simple heuristic:
    0 = clean
    1 = mild (1–2 bad words)
    2 = strong (3–4 bad words)
    3 = extreme (5+ bad words)
    """
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 4:
        return 2
    return 3


def analyze_text(text: str) -> TextModerationResult:
    """
    Analyze a single text string (e.g. one chunk of transcript).
    """
    found = find_bad_words_in_text(text)
    count = len(found)
    severity = _compute_severity(count)

    # For now: block only on strong profanity.
    block = severity >= 2

    return TextModerationResult(
        original_text=text,
        bad_words=found,
        count=count,
        severity=severity,
        block=block,
    )



def analyze_transcript(chunks: List[str]) -> TextModerationResult:
    """
    Analyze a full transcript represented as list of text chunks.
    Joins them and applies the same logic.
    """
    joined = " ".join(chunks)
    return analyze_text(joined)
