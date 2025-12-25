from typing import List, Dict, Tuple
from src.aegisai.moderation.bad_words_list import is_bad_word
Interval = Tuple[float, float]


def detect_toxic_segments(
    words: List[Dict],
    padding: float = 0.15,
    max_gap: float = 0.25,
) -> List[Tuple[float, float]]:
    """
    From word-level timestamps, return continuous toxic segments in *local*
    chunk time.

    Implements 'smart padding': extends the mute interval to cover the silence
    gap up to the neighboring words (with a safety margin).
    """
    segments: List[Tuple[float, float]] = []
    current_start = None
    current_end = None

    for i, w in enumerate(words):
        token = w.get("word", "")
        if is_bad_word(token):
            # Start logic: look at previous word end
            start_val = float(w["start"])
            if i > 0:
                prev_end = float(words[i-1]["end"])
                # Mute starts slightly after previous word ends (e.g. 50ms buffer)
                # or midway if gap is very small.
                # Here we ensure we mute the silence but don't clip previous word.
                seg_start = prev_end + 0.05
                # If calculated start is after the bad word start (unlikely but possible with overlap), clamp it.
                # Actually, we want to mute BEFORE the bad word.
                # Standard padding fallback:
                if seg_start > start_val:
                    seg_start = start_val - padding
                else:
                    # ensure we don't go back too far if gap is huge (cap at 2.0s extension)
                    seg_start = max(seg_start, start_val - 2.0)
            else:
                seg_start = max(0.0, start_val - padding)

            # End logic: look at next word start
            end_val = float(w["end"])
            if i < len(words) - 1:
                next_start = float(words[i+1]["start"])
                # Mute ends slightly before next word starts
                seg_end = next_start - 0.05
                # Fallback if gap is tiny or negative
                if seg_end < end_val:
                    seg_end = end_val + padding
                else:
                    # ensure we don't extend too far if gap is huge (cap at 2.0s extension)
                    seg_end = min(seg_end, end_val + 2.0)
            else:
                seg_end = end_val + padding

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



def merge_intervals(
    intervals: List[Interval], 
    gap_threshold: float = 0.0,
) -> List[Interval]:
    """
    Merge overlapping or adjacent [start, end] intervals.
    
    Args:
        intervals: List of (start, end) time intervals
        gap_threshold: Also merge intervals within this gap (seconds).
                       Default 0.0 means only merge overlapping/touching intervals.
                       
    Returns:
        List of merged intervals, sorted by start time.
    """
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: x[0])
    merged: List[Interval] = []
    cur_start, cur_end = intervals[0]

    for start, end in intervals[1:]:
        # Merge if overlapping, touching, or within gap threshold
        if start <= cur_end + gap_threshold:
            cur_end = max(cur_end, end)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end

    merged.append((cur_start, cur_end))
    return merged
