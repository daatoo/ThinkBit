# Optimization Report – Top-k Blocklist & Prompt Reduction

## Evaluation Setup
- **Dataset:** 60 synthetic transcripts (35 profane, 15 clean, 10 edge cases).
- **Baseline path:** Full blocklist, 80-token system prompt, response buffer 85.
- **Optimized path:** Deduplicated + top-20 relevant blocklist, 15-token system prompt, same buffer.
- **Cost model:** GPT-4 Turbo input $10 / 1M tokens.
- **Latency:** Local function timing (no external API).

## Baseline Metrics
| Metric | Value |
| --- | --- |
| Avg tokens / request | 635.9 |
| Total cost (60 req) | $0.3816 |
| P95 latency | 0.281 ms |
| Precision | 0.953 |
| Recall | 0.976 |

## Optimized Metrics
| Metric | Value |
| --- | --- |
| Avg tokens / request | 126.0 |
| Total cost (60 req) | $0.0756 |
| P95 latency | 0.026 ms |
| Precision | 0.953 |
| Recall | 0.976 |

## Final deltas
- **Cost reduction:** 80.19%  
  Formula: `(0.3816 - 0.0756) / 0.3816 * 100`
- **Latency change (p95):** -0.255 ms (optimized is faster)
- **Quality impact:** Precision/recall unchanged on the 60-query run; no optimized-only misses.

## Edge cases observed
- Hyphenated profanity like `mother-fucker` is still missed because regex uses strict word boundaries.
- Split slang such as `dumb-ass` also slips past detection for the same reason.
- Obfuscated strings (`f@ck`, `sh1t`) remain out-of-scope for the current blocklist heuristics.

## What worked
- Deduplicating and scoring the blocklist before scanning cut blocklist tokens by ~80% without hurting precision/recall.
- Shorter system prompt (80 → 15 tokens) plus the lean blocklist dropped total tokens/request by ~5x.
- Latency improved slightly because the regex scan iterates over far fewer candidates per query.

## What didn’t / risks
- Hyphen/spacing variants and leetspeak remain false negatives; need additional normalization or fuzzy matching to close the gap.
- Relevance scoring is substring-based; highly short transcripts with no hints fall back to the top-k slice, which could still miss rare terms.

## Key code changes
Top-k blocklist selector (k=20) with dedup fallback:
```python
def get_relevant_blocklist(transcript: str, blocklist: Sequence[str], k: int = 20) -> List[str]:
    normalized_transcript = transcript.lower()
    scored = []
    for word in blocklist:
        w_norm = word.lower()
        score = 0
        if w_norm in normalized_transcript:
            score += 10
        score += normalized_transcript.count(w_norm)
        if score > 0:
            scored.append((score, word))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return list(blocklist[:k]) if isinstance(blocklist, list) else list(blocklist)[:k]
    return [word for _, word in scored[:k]]
```

Optimized analyzer wired into text moderation:
```python
def analyze_text_top_k(text: str, base_blocklist: Iterable[str] | None = None, k: int = 20) -> TextModerationResult:
    blocklist_source = list(base_blocklist) if base_blocklist is not None else list(BAD_WORDS)
    deduped = deduplicate_blocklist(blocklist_source)
    relevant = get_relevant_blocklist(text, deduped, k=k)
    if not relevant:
        relevant = deduped[:k]
    return analyze_text(text, blocklist=relevant)
```

Evaluation harness (60 queries, prints metrics):
```python
# scripts/optimization_eval.py
results = evaluate()
print(f"Queries evaluated: {len(results['cases'])}")
print(f"Baseline avg tokens/request: {avg_tokens_baseline:.1f}")
print(f"Optimized avg tokens/request: {avg_tokens_opt:.1f}")
print(f"P95 latency baseline: {p95_base:.3f} ms")
print(f"P95 latency optimized: {p95_opt:.3f} ms")
```

