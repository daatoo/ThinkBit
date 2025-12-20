"""
Text moderation rules: bad words / profanity detection.
"""

from dataclasses import dataclass
from typing import List, Iterable
from .bad_words_list import BAD_WORDS
import re

from .bad_words_list import find_bad_words_in_text
from .optimization import deduplicate_blocklist, get_relevant_blocklist


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


def analyze_text(text: str, blocklist: Iterable[str] | None = None, strict: bool = False) -> TextModerationResult:
    """
    Analyze a single text string (e.g. one chunk of transcript).
    """
    found = find_bad_words_in_text(text, blocklist)
    count = len(found)
    severity = _compute_severity(count)

    # For now: block only on strong profanity.
    # If strict is True, block on ANY bad word.
    if strict:
        block = count > 0
    else:
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


def analyze_text_top_k(
    text: str,
    base_blocklist: Iterable[str] | None = None,
    k: int = 20,
) -> TextModerationResult:
    """
    Optimized version that reduces the scanning blocklist to the
    top-k words most relevant to the transcript. This mirrors the
    token-reduction strategy described in docs/token-cost-optimization.md.
    """
    blocklist_source = list(base_blocklist) if base_blocklist is not None else list(BAD_WORDS)
    deduped = deduplicate_blocklist(blocklist_source)
    relevant = get_relevant_blocklist(text, deduped, k=k)

    # Fallback: keep a small slice to avoid empty matching lists
    if not relevant:
        relevant = deduped[:k]

    return analyze_text(text, blocklist=relevant)
