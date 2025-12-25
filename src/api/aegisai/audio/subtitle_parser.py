import re
from typing import List, Dict, TypedDict

class SubtitleSegment(TypedDict):
    start: float
    end: float
    text: str

def _parse_timestamp(ts_str: str) -> float:
    """
    Parse timestamp string to seconds.
    Formats: HH:MM:SS,mmm or HH:MM:SS.mmm or MM:SS.mmm (VTT)
    """
    ts_str = ts_str.replace(',', '.')
    parts = ts_str.split(':')

    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    else:
        raise ValueError(f"Invalid timestamp format: {ts_str}")

def parse_subtitle_file(path: str) -> List[SubtitleSegment]:
    """
    Parse SRT or VTT file and return segments.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    segments: List[SubtitleSegment] = []

    # Unified regex for SRT and VTT timestamps
    ts_pattern = re.compile(r'((?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{3})\s-->\s((?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{3})')
    # Regex for integer line (SRT index)
    index_pattern = re.compile(r'^\d+$')

    lines = content.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        # Check for timestamp line
        match = ts_pattern.search(line)
        if match:
            try:
                start_time = _parse_timestamp(match.group(1))
                end_time = _parse_timestamp(match.group(2))

                # Extract text
                text_lines = []
                i += 1
                while i < n:
                    next_line = lines[i].strip()

                    # Stop conditions:

                    # 1. Empty line (Block separator)
                    if not next_line:
                        break

                    # 2. Next line is a timestamp (VTT no-blank-line case)
                    if ts_pattern.search(next_line):
                        break

                    # 3. Next line is a number AND the line AFTER that is a timestamp (SRT no-blank-line case)
                    # We need to peek 2 lines ahead effectively.
                    if index_pattern.match(next_line):
                        # Look ahead one more line if possible
                        if i + 1 < n:
                            after_next = lines[i+1].strip()
                            if ts_pattern.search(after_next):
                                # 'next_line' is an index, so we stop here.
                                break

                    text_lines.append(next_line)
                    i += 1

                text = " ".join(text_lines).strip()
                text = re.sub(r'<[^>]+>', '', text) # Strip tags

                segments.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text
                })

                continue

            except ValueError:
                pass

        i += 1

    return segments
