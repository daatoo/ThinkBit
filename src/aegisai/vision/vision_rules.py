from .label_lists import VIOLENCE_LABELS
from .safe_search import Likelihood


def classify_safesearch(result):
    """
    result: SafeSearchResult from safe_search.py
    """
    adult = result.adult.value
    violence = result.violence.value
    racy = result.racy.value

    # Block when SafeSearch is LIKELY or VERY_LIKELY
    block = (
        adult >= Likelihood.LIKELY or
        violence >= Likelihood.LIKELY or
        racy >= Likelihood.VERY_LIKELY
    )

    return {
        "adult": adult,
        "violence": violence,
        "racy": racy,
        "block": block,
    }

def classify_labels(labels, threshold=0.60):
    """
    labels: output from analyze_labels()
    threshold: minimum score to consider relevant
    """
    for item in labels:
        desc = item["description"]
        score = item["score"]

        # Check if label is a violence-related keyword
        if desc in VIOLENCE_LABELS and score >= threshold:
            return {
                "violence_detected": True,
                "label": desc,
                "score": score,
                "block": True
            }

    return {
        "violence_detected": False,
        "block": False
    }


from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class FrameModerationResult:
    """
    Safety decision for a *single* video frame.
    """
    timestamp: float
    safesearch: dict      # output of classify_safesearch()
    labels: dict          # output of classify_labels()
    block: bool           # final per-frame decision: True => unsafe


def combine_frame_decision(
    timestamp: float,
    safesearch_info: dict,
    labels_info: dict,
) -> FrameModerationResult:
    """
    Combine SafeSearch + violence labels into one per-frame decision.

    Current logic:
      - block if either safesearch.block or labels.block is True
    """
    block = bool(safesearch_info.get("block") or labels_info.get("block"))
    # print(
    #     f"[combine_frame_decision] Frame at t={timestamp:.2f}s: "
    #     f"safesearch_block={safesearch_info.get('block')}, "
    #     f"labels_block={labels_info.get('block')} -> final_block={block}"
    # )
    return FrameModerationResult(
        timestamp=timestamp,
        safesearch=safesearch_info,
        labels=labels_info,
        block=block,
    )


def intervals_from_frames(
    frames: List[FrameModerationResult],
    frame_step: float,
) -> List[Tuple[float, float]]:
    """
    Convert per-frame block/ok decisions into time intervals.

    frame_step = seconds between sampled frames (e.g. 1 / sample_fps).
    """
    intervals: List[Tuple[float, float]] = []
    current_start: float | None = None

    for f in frames:
        if f.block:
            if current_start is None:
                current_start = f.timestamp
        else:
            if current_start is not None:
                end = f.timestamp + frame_step
                intervals.append((current_start, end))
                current_start = None

    # If stream ended in a blocked region, close it
    if current_start is not None and frames:
        last_ts = frames[-1].timestamp
        intervals.append((current_start, last_ts + frame_step))

    return intervals