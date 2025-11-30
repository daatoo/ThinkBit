from src.aegisai.vision.label_lists import VIOLENCE_LABELS
from src.aegisai.vision.safe_search import Likelihood


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