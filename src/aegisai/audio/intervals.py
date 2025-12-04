from typing import List, Dict, Tuple
from src.aegisai.moderation.bad_words_list import is_bad_word

def detect_toxic_segments(
    words: List[Dict],
    padding: float = 0.15,
    max_gap: float = 0.25,
) -> List[Tuple[float, float]]:
    """
    From word-level timestamps, return continuous toxic segments in *local*
    chunk time.
    """
    segments: List[Tuple[float, float]] = []
    current_start = None
    current_end = None

    for w in words:
        token = w.get("word", "")
        if is_bad_word(token):
            seg_start = max(0.0, float(w["start"]) - padding)
            seg_end = float(w["end"]) + padding

            if current_start is None:
                current_start = seg_start
                current_end = seg_end
            else:
                if seg_start <= current_end + max_gap:
                    current_end = max(current_end, seg_end)
                else:
                    segments.append((current_start, current_end))
                    current_start = seg_start
                    current_end = seg_end

    if current_start is not None:
        segments.append((current_start, current_end))

    return segments
