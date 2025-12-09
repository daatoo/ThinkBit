"""
Run a synthetic evaluation of the token-cost optimization (top-k blocklist +
prompt reduction) described in docs/token-cost-optimization.md.

The script:
- builds 60 test transcripts (50+ as requested)
- compares baseline detection (full blocklist) vs optimized (top-k blocklist)
- reports token usage, estimated cost, latency (p95), and precision/recall
"""

from __future__ import annotations

import math
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Set

# Allow running as a standalone script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.aegisai.moderation.bad_words_list import BAD_WORDS, find_bad_words_in_text
from src.aegisai.moderation.optimization import (
    calculate_request_tokens,
    deduplicate_blocklist,
    estimate_tokens,
    get_relevant_blocklist,
)

random.seed(1337)

BASELINE_PROMPT_TOKENS = 80
OPT_PROMPT_TOKENS = 15
RESPONSE_BUFFER = 85
TOP_K = 20
COST_PER_TOKEN = 10 / 1_000_000  # $10 per 1M input tokens (GPT-4 Turbo)


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, math.ceil(pct * len(ordered)) - 1))
    return ordered[k]


def _build_dataset() -> List[dict]:
    filler = [
        "please consider",
        "the quick brown fox",
        "background noise in clip",
        "user said quietly",
        "conversation continued",
        "context window sample",
    ]

    profane_words = [
        "fuck",
        "shit",
        "bitch",
        "asshole",
        "damn",
        "pissed",
        "motherfucker",
        "wtf",
        "dumbass",
        "hell",
        "prick",
        "jerk",
        "trash",
        "idiot",
    ]

    dataset: List[dict] = []

    # 35 profanity-heavy samples
    for i in range(35):
        n = random.randint(1, 3)
        chosen = random.sample(profane_words, n)
        text = (
            f"{random.choice(filler)} {chosen[0]} {random.choice(filler)} "
            f"{' '.join(chosen[1:]) if len(chosen) > 1 else ''}"
        )
        dataset.append(
            {
                "id": f"profanity-{i+1}",
                "text": text.strip(),
                "expected": set(chosen),
            }
        )

    # 15 clean samples
    clean_phrases = [
        "family friendly content with zero issues",
        "background music only no speech",
        "educational lecture about history",
        "cooking show recipe for pancakes",
        "kids cartoon with happy songs",
    ]
    for i in range(15):
        text = random.choice(clean_phrases) + " " + random.choice(filler)
        dataset.append({"id": f"clean-{i+1}", "text": text, "expected": set()})

    # 10 edge cases
    edge_cases = [
        ("EDGE-UPPER", "FUCK this is shouted text", {"fuck"}),
        ("EDGE-HYPHEN", "mother-fucker tries to slip through", {"motherfucker"}),
        ("EDGE-PUNCT", "what the... shit!!!", {"shit"}),
        ("EDGE-SPACED", "f u c k spelled out slowly", set()),
        ("EDGE-OBFUSCATED", "f@ck and sh1t typed to avoid filters", set()),
        ("EDGE-SLANG", "this dude is such a dumb-ass", {"dumbass"}),
        ("EDGE-RUNON", "hellishhell scenario but only one hell counts", {"hell"}),
        ("EDGE-MULTI", "jerk and asshole plus bitch together", {"jerk", "asshole", "bitch"}),
        ("EDGE-LONG", " ".join(random.choice(filler) for _ in range(20)), set()),
        ("EDGE-NONE", "totally benign and calm dialogue no problems here", set()),
    ]
    for ident, text, expected in edge_cases:
        dataset.append({"id": ident, "text": text, "expected": set(expected)})

    return dataset


def _confusion(found: Set[str], expected: Set[str]) -> tuple[int, int, int]:
    tp = len(found & expected)
    fp = len(found - expected)
    fn = len(expected - found)
    return tp, fp, fn


def evaluate() -> dict:
    cases = _build_dataset()
    full_blocklist = list(BAD_WORDS)
    deduped_blocklist = deduplicate_blocklist(full_blocklist)

    stats = {
        "baseline_tokens": [],
        "optimized_tokens": [],
        "baseline_times": [],
        "optimized_times": [],
        "baseline_confusion": [0, 0, 0],  # tp, fp, fn
        "optimized_confusion": [0, 0, 0],
        "misses": [],
    }

    for case in cases:
        text = case["text"]
        expected = case["expected"]

        # Baseline: full blocklist
        t0 = time.perf_counter()
        baseline_found = set(find_bad_words_in_text(text, full_blocklist))
        stats["baseline_times"].append(time.perf_counter() - t0)

        # Optimized: dedup + top-k
        rel_blocklist = get_relevant_blocklist(text, deduped_blocklist, k=TOP_K)
        t1 = time.perf_counter()
        optimized_found = set(find_bad_words_in_text(text, rel_blocklist))
        stats["optimized_times"].append(time.perf_counter() - t1)

        # Tokens
        stats["baseline_tokens"].append(
            calculate_request_tokens(
                transcript=text,
                blocklist=full_blocklist,
                system_prompt_tokens=BASELINE_PROMPT_TOKENS,
                response_buffer=RESPONSE_BUFFER,
            )
        )
        stats["optimized_tokens"].append(
            calculate_request_tokens(
                transcript=text,
                blocklist=rel_blocklist,
                system_prompt_tokens=OPT_PROMPT_TOKENS,
                response_buffer=RESPONSE_BUFFER,
            )
        )

        # Confusion tallies
        tp, fp, fn = _confusion(baseline_found, expected)
        stats["baseline_confusion"][0] += tp
        stats["baseline_confusion"][1] += fp
        stats["baseline_confusion"][2] += fn

        tp_o, fp_o, fn_o = _confusion(optimized_found, expected)
        stats["optimized_confusion"][0] += tp_o
        stats["optimized_confusion"][1] += fp_o
        stats["optimized_confusion"][2] += fn_o

        # Track misses where optimized lost a detection baseline caught
        if baseline_found and (baseline_found - optimized_found):
            stats["misses"].append(
                {
                    "id": case["id"],
                    "expected": sorted(expected),
                    "baseline_found": sorted(baseline_found),
                    "optimized_found": sorted(optimized_found),
                    "optimized_blocklist_size": len(rel_blocklist),
                }
            )

    return {"cases": cases, **stats}


def _precision_recall(confusion: Sequence[int]) -> tuple[float, float]:
    tp, fp, fn = confusion
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return precision, recall


def main() -> None:
    results = evaluate()
    n = len(results["cases"])

    avg_tokens_baseline = statistics.mean(results["baseline_tokens"])
    avg_tokens_opt = statistics.mean(results["optimized_tokens"])

    total_cost_baseline = sum(results["baseline_tokens"]) * COST_PER_TOKEN
    total_cost_opt = sum(results["optimized_tokens"]) * COST_PER_TOKEN

    p95_base = percentile(results["baseline_times"], 0.95) * 1000
    p95_opt = percentile(results["optimized_times"], 0.95) * 1000

    prec_b, rec_b = _precision_recall(results["baseline_confusion"])
    prec_o, rec_o = _precision_recall(results["optimized_confusion"])

    cost_reduction_pct = (
        (total_cost_baseline - total_cost_opt) / total_cost_baseline * 100
        if total_cost_baseline
        else 0.0
    )

    print("=== Token Cost Optimization Evaluation ===")
    print(f"Queries evaluated: {n}")
    print(f"Baseline avg tokens/request: {avg_tokens_baseline:.1f}")
    print(f"Optimized avg tokens/request: {avg_tokens_opt:.1f}")
    print(f"Baseline total cost (USD): ${total_cost_baseline:.4f}")
    print(f"Optimized total cost (USD): ${total_cost_opt:.4f}")
    print(f"Cost reduction: {cost_reduction_pct:.2f}%")
    print(f"P95 latency baseline: {p95_base:.3f} ms")
    print(f"P95 latency optimized: {p95_opt:.3f} ms")
    print(f"Latency delta (opt - base): {p95_opt - p95_base:.3f} ms")
    print(f"Precision baseline/optimized: {prec_b:.3f} / {prec_o:.3f}")
    print(f"Recall    baseline/optimized: {rec_b:.3f} / {rec_o:.3f}")
    print(f"Optimized misses vs baseline: {len(results['misses'])}")

    if results["misses"]:
        print("\nSample misses (optimized lost detections):")
        for miss in results["misses"][:5]:
            print(
                f"- {miss['id']}: expected={miss['expected']} "
                f"baseline_found={miss['baseline_found']} "
                f"optimized_found={miss['optimized_found']} "
                f"(blocklist size={miss['optimized_blocklist_size']})"
            )


if __name__ == "__main__":
    main()

