"""
Utilities for token/cost optimization when sending transcripts + blocklists
to LLMs. Implements the strategies outlined in docs/token-cost-optimization.md:
- top-k blocklist selection
- blocklist deduplication
- simple token estimation helpers
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence

from .bad_words_list import normalize_text_for_matching


def estimate_tokens(text: str) -> int:
    """
    Lightweight token estimator (roughly 4 chars per token).
    Good enough for comparative cost calculations without an external tokenizer.
    """
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def deduplicate_blocklist(blocklist: Iterable[str]) -> List[str]:
    """
    Remove near-duplicate profanity variants to shrink prompt/context.
    Normalizes by lowercasing and stripping non-alphanumerics.
    """
    seen = set()
    deduped: List[str] = []
    for word in blocklist:
        normalized = "".join(ch for ch in word.lower() if ch.isalnum() or ch.isspace()).strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(word)
    return deduped


def get_relevant_blocklist(
    transcript: str,
    blocklist: Sequence[str],
    k: int = 20,
) -> List[str]:
    """
    Rank blocklist terms by likelihood of appearing in transcript and return top-k.

    Heuristic scoring:
    - substring presence (+10)
    - raw frequency count (+n)
    """
    normalized_transcript = transcript.lower()
    scored: List[tuple[int, str]] = []

    for word in blocklist:
        w_norm = word.lower()
        score = 0
        if w_norm in normalized_transcript:
            score += 10
        score += normalized_transcript.count(w_norm)
        if score > 0:
            scored.append((score, word))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If nothing scored (clean transcript), still return a small slice
    if not scored:
        return list(blocklist[:k]) if isinstance(blocklist, list) else list(blocklist)[:k]

    return [word for _, word in scored[:k]]


def calculate_request_tokens(
    transcript: str,
    blocklist: Sequence[str],
    system_prompt_tokens: int,
    response_buffer: int = 85,
) -> int:
    """
    Estimate total tokens for one request (prompt + transcript + blocklist + response buffer).
    """
    transcript_tokens = estimate_tokens(transcript)
    blocklist_tokens = estimate_tokens(" ".join(blocklist))
    return system_prompt_tokens + transcript_tokens + blocklist_tokens + response_buffer

