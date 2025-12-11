from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Set

import cv2
import numpy as np

from src.aegisai.video.ffmpeg_edit import blur_boxes_in_frame

Interval = Tuple[float, float]
Box = Tuple[int, int, int, int]

# ─────────────────────────────────────────────────────────
# Configuration for improved regional blocking accuracy
# ─────────────────────────────────────────────────────────
BBOX_EXPANSION_RATIO = 0.25      # Expand boxes by 25% for better coverage
BBOX_MIN_EXPANSION_PX = 15       # Minimum expansion in pixels
TEMPORAL_WINDOW_FRAMES = 5       # Look at ±5 sample frames for tracking
IOU_MATCH_THRESHOLD = 0.15       # Lower threshold for matching tracked objects
CENTER_DISTANCE_THRESHOLD = 0.3  # Max center distance (relative to frame diagonal)
PERSISTENCE_FRAMES = 3           # Keep boxes for N frames after last detection


@dataclass
class TrackedObject:
    """
    Represents a tracked object across multiple frames.
    """
    object_id: int
    label: str
    boxes_history: List[Tuple[float, Box]] = field(default_factory=list)  # (timestamp, box)
    last_seen_ts: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    
    def add_detection(self, ts: float, box: Box, confidence: float = 0.0):
        """Add a new detection to this object's history."""
        self.boxes_history.append((ts, box))
        self.last_seen_ts = ts
        if confidence > 0:
            self.confidence = max(self.confidence, confidence)
    
    def get_interpolated_box(self, ts: float, frame_width: int, frame_height: int) -> Optional[Box]:
        """
        Get interpolated/extrapolated box for a given timestamp.
        Uses linear interpolation between known positions.
        """
        if not self.boxes_history:
            return None
        
        # Sort by timestamp
        sorted_history = sorted(self.boxes_history, key=lambda x: x[0])
        
        # Find bracketing timestamps
        prev_entry = None
        next_entry = None
        
        for entry in sorted_history:
            if entry[0] <= ts:
                prev_entry = entry
            if entry[0] > ts and next_entry is None:
                next_entry = entry
                break
        
        # If exact match, return that box
        for entry in sorted_history:
            if abs(entry[0] - ts) < 0.001:
                return entry[1]
        
        # Interpolation
        if prev_entry and next_entry:
            t_factor = (ts - prev_entry[0]) / (next_entry[0] - prev_entry[0]) if next_entry[0] != prev_entry[0] else 0.5
            return _interpolate_box(prev_entry[1], next_entry[1], t_factor)
        
        # Extrapolation (use last known position with small expansion)
        if prev_entry:
            # Use last known box
            return prev_entry[1]
        
        if next_entry:
            return next_entry[1]
        
        return None


def _timestamp_in_intervals(ts: float, intervals: List[Interval]) -> bool:
    for start, end in intervals:
        if start <= ts <= end:
            return True
    return False


def _expand_bbox(
    box: Box, 
    width: int, 
    height: int, 
    expansion_ratio: float = BBOX_EXPANSION_RATIO,
    min_expansion_px: int = BBOX_MIN_EXPANSION_PX,
) -> Box:
    """
    Expand a bounding box adaptively based on size and frame dimensions.
    
    Uses both percentage-based and minimum pixel expansion to ensure
    adequate coverage for both small and large objects.
    
    Args:
        box: (x1, y1, x2, y2) bounding box
        width: Frame width for clamping
        height: Frame height for clamping
        expansion_ratio: Percentage expansion (0.25 = 25% on each side)
        min_expansion_px: Minimum expansion in pixels
    
    Returns:
        Expanded bounding box clamped to frame dimensions
    """
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    
    # Calculate expansion: max of percentage-based and minimum pixel
    expand_x = max(int(box_width * expansion_ratio), min_expansion_px)
    expand_y = max(int(box_height * expansion_ratio), min_expansion_px)
    
    # Apply expansion and clamp to frame bounds
    new_x1 = max(0, x1 - expand_x)
    new_y1 = max(0, y1 - expand_y)
    new_x2 = min(width, x2 + expand_x)
    new_y2 = min(height, y2 + expand_y)
    
    return (new_x1, new_y1, new_x2, new_y2)


def _interpolate_box(box1: Box, box2: Box, t: float) -> Box:
    """
    Linear interpolation between two bounding boxes.
    
    Args:
        box1: First bounding box (x1, y1, x2, y2)
        box2: Second bounding box (x1, y1, x2, y2)
        t: Interpolation factor (0.0 = box1, 1.0 = box2)
    
    Returns:
        Interpolated bounding box
    """
    # Clamp t to [0, 1] range
    t = max(0.0, min(1.0, t))
    return (
        int(box1[0] + (box2[0] - box1[0]) * t),
        int(box1[1] + (box2[1] - box1[1]) * t),
        int(box1[2] + (box2[2] - box1[2]) * t),
        int(box1[3] + (box2[3] - box1[3]) * t),
    )


def _box_center(box: Box) -> Tuple[float, float]:
    """Get center point of a bounding box."""
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _box_area(box: Box) -> int:
    """Calculate area of bounding box."""
    return max(0, (box[2] - box[0]) * (box[3] - box[1]))


def _calculate_iou(box1: Box, box2: Box) -> float:
    """Calculate Intersection over Union between two boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x1 >= x2 or y1 >= y2:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = _box_area(box1)
    area2 = _box_area(box2)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def _calculate_center_distance(box1: Box, box2: Box, frame_diag: float) -> float:
    """
    Calculate normalized center distance between two boxes.
    Returns value between 0 (same center) and 1+ (far apart).
    """
    c1 = _box_center(box1)
    c2 = _box_center(box2)
    dist = ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)**0.5
    return dist / frame_diag if frame_diag > 0 else 0.0


def _find_matching_box(
    target: Box, 
    candidates: List[Box], 
    frame_diag: float,
    iou_threshold: float = IOU_MATCH_THRESHOLD,
    center_threshold: float = CENTER_DISTANCE_THRESHOLD,
) -> Optional[Box]:
    """
    Find the best matching box from candidates using combined IoU and center distance.
    
    Args:
        target: Box to match
        candidates: List of candidate boxes
        frame_diag: Frame diagonal for normalizing center distance
        iou_threshold: Minimum IoU to consider a match
        center_threshold: Maximum center distance (normalized)
    
    Returns:
        Best matching box or None if no match
    """
    if not candidates:
        return None
    
    best_match = None
    best_score = 0.0
    
    for cand in candidates:
        iou = _calculate_iou(target, cand)
        center_dist = _calculate_center_distance(target, cand, frame_diag)
        
        # Combined score: IoU weighted + inverse center distance
        if iou > 0 or center_dist < center_threshold:
            # Score formula: IoU + (1 - normalized_center_distance) * 0.5
            score = iou + max(0, 1 - center_dist / center_threshold) * 0.5
            
            if score > best_score:
                best_score = score
                best_match = cand
    
    return best_match


def _merge_overlapping_boxes(boxes: List[Box], iou_threshold: float = 0.3) -> List[Box]:
    """
    Merge significantly overlapping boxes into single larger boxes.
    This prevents blur artifacts from overlapping regions.
    """
    if len(boxes) <= 1:
        return boxes
    
    merged = []
    used = [False] * len(boxes)
    
    for i, box1 in enumerate(boxes):
        if used[i]:
            continue
        
        # Find all boxes that overlap with box1
        group = [box1]
        used[i] = True
        
        for j, box2 in enumerate(boxes):
            if used[j]:
                continue
            
            # Check if box2 overlaps with any box in the group
            for gbox in group:
                if _calculate_iou(gbox, box2) > iou_threshold:
                    group.append(box2)
                    used[j] = True
                    break
        
        # Merge group into single box
        if group:
            min_x1 = min(b[0] for b in group)
            min_y1 = min(b[1] for b in group)
            max_x2 = max(b[2] for b in group)
            max_y2 = max(b[3] for b in group)
            merged.append((min_x1, min_y1, max_x2, max_y2))
    
    return merged


def _build_sample_lookup(
    object_boxes: List[Dict[str, Any]],
) -> Dict[float, List[Tuple[Box, str, str, float]]]:
    """
    Build lookup from timestamp to list of (box, label, reason, confidence).
    
    object_boxes example:
      [{"timestamp": 10.0, "boxes": [(x1,y1,x2,y2), ...], "labels": [...], "reasons": [...]}, ...]
    """
    lookup: Dict[float, List[Tuple[Box, str, str, float]]] = {}
    
    for entry in object_boxes:
        ts = float(entry["timestamp"])
        key = round(ts, 3)
        
        boxes = entry.get("boxes", [])
        labels = entry.get("labels", ["unknown"] * len(boxes))
        reasons = entry.get("reasons", ["unknown"] * len(boxes))
        confidences = entry.get("confidences", [1.0] * len(boxes))
        
        # Pad lists if needed
        while len(labels) < len(boxes):
            labels.append("unknown")
        while len(reasons) < len(boxes):
            reasons.append("unknown")
        while len(confidences) < len(boxes):
            confidences.append(1.0)
        
        for i, box in enumerate(boxes):
            box_tuple = tuple(box) if not isinstance(box, tuple) else box
            lookup.setdefault(key, []).append((
                box_tuple,
                labels[i] if i < len(labels) else "unknown",
                reasons[i] if i < len(reasons) else "unknown",
                confidences[i] if i < len(confidences) else 1.0,
            ))
    
    return lookup


def _build_tracked_objects(
    sample_lookup: Dict[float, List[Tuple[Box, str, str, float]]],
    frame_width: int,
    frame_height: int,
) -> List[TrackedObject]:
    """
    Build tracked objects by linking detections across frames.
    This provides temporal consistency for blur regions.
    """
    frame_diag = (frame_width**2 + frame_height**2)**0.5
    sorted_timestamps = sorted(sample_lookup.keys())
    
    tracked_objects: List[TrackedObject] = []
    next_id = 0
    
    for ts in sorted_timestamps:
        detections = sample_lookup.get(ts, [])
        
        for box, label, reason, conf in detections:
            # Try to match with existing tracked object
            best_match_obj = None
            best_match_score = 0.0
            
            for tracked in tracked_objects:
                # Get last known position
                if not tracked.boxes_history:
                    continue
                
                last_ts, last_box = tracked.boxes_history[-1]
                
                # Don't match if too old
                if ts - last_ts > 2.0:  # 2 second threshold
                    continue
                
                # Calculate match score
                iou = _calculate_iou(box, last_box)
                center_dist = _calculate_center_distance(box, last_box, frame_diag)
                
                if iou > 0.1 or center_dist < 0.2:
                    score = iou + max(0, 1 - center_dist * 2) * 0.5
                    
                    # Same label gets bonus
                    if tracked.label.lower() == label.lower():
                        score += 0.3
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match_obj = tracked
            
            if best_match_obj and best_match_score > 0.3:
                # Update existing tracked object
                best_match_obj.add_detection(ts, box, conf)
            else:
                # Create new tracked object
                new_obj = TrackedObject(
                    object_id=next_id,
                    label=label,
                    reason=reason,
                    confidence=conf,
                )
                new_obj.add_detection(ts, box, conf)
                tracked_objects.append(new_obj)
                next_id += 1
    
    return tracked_objects


def blur_moving_objects_with_intervals(
    video_path: str | Path,
    intervals: List[Interval],
    object_boxes: List[Dict[str, Any]],
    sample_fps: float,
    output_video_path: str | Path,
    blur_ksize: int = 55,            # Stronger blur for better obscuring
    expand_boxes: bool = True,        # Expand bounding boxes for better coverage
    interpolate_boxes: bool = True,   # Interpolate boxes between samples
    use_tracking: bool = True,        # Use object tracking for consistency
    expansion_ratio: float = BBOX_EXPANSION_RATIO,
) -> None:
    """
    Blur moving objects with improved temporal tracking and coverage.
    
    Key improvements:
    1. Object tracking: Links detections across frames for consistent blur
    2. Adaptive expansion: Expands boxes based on size with minimum pixels
    3. Temporal interpolation: Smooth box transitions between samples
    4. Multi-frame aggregation: Aggregates from nearby sample frames
    5. Box merging: Merges overlapping boxes to prevent artifacts
    6. Persistence: Maintains blur for a few frames after object disappears

    Args:
        video_path: Original video with audio
        intervals: Merged unsafe intervals [(start, end), ...]
        object_boxes: Per-sampled-frame detection result
        sample_fps: FPS used when sampling frames for Vision (e.g. 6.0)
        output_video_path: Final output with blurred video + original audio
        blur_ksize: Blur kernel size (higher = stronger blur)
        expand_boxes: Whether to expand bounding boxes for better coverage
        interpolate_boxes: Whether to interpolate boxes between sample frames
        use_tracking: Whether to use object tracking for temporal consistency
        expansion_ratio: Box expansion ratio (default 0.25 = 25%)
    """
    video_path = Path(video_path).expanduser().resolve()
    output_video_path = Path(output_video_path).expanduser().resolve()

    if not intervals:
        # Nothing unsafe: just copy
        shutil.copy2(video_path, output_video_path)
        return

    # Build sample lookup
    sample_lookup = _build_sample_lookup(object_boxes)
    sorted_timestamps = sorted(sample_lookup.keys())
    
    if not sorted_timestamps:
        # No detections, but we have intervals - apply full-frame blur
        print("[region_blur] Warning: No object boxes detected, copying original video")
        shutil.copy2(video_path, output_video_path)
        return

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_diag = (width**2 + height**2)**0.5
    
    # Build tracked objects if tracking is enabled
    tracked_objects: List[TrackedObject] = []
    if use_tracking:
        tracked_objects = _build_tracked_objects(sample_lookup, width, height)
        print(f"[region_blur] Tracking {len(tracked_objects)} objects across video")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    with tempfile.TemporaryDirectory(prefix="aegis_objblur_") as tmpdir:
        tmpdir = Path(tmpdir)
        temp_video_noaudio = tmpdir / "video_blurred_noaudio.mp4"

        out = cv2.VideoWriter(
            str(temp_video_noaudio),
            fourcc,
            fps,
            (width, height),
        )

        if not out.isOpened():
            cap.release()
            raise RuntimeError("Failed to open VideoWriter")

        frame_idx = 0
        sample_period = 1.0 / sample_fps
        persistence_period = PERSISTENCE_FRAMES * sample_period
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            ts = frame_idx / fps  # timestamp in seconds

            # Only blur if we're inside an unsafe interval
            if _timestamp_in_intervals(ts, intervals):
                boxes: List[Box] = []
                
                # ─────────────────────────────────────────────────────────
                # Method 1: Object tracking (preferred)
                # ─────────────────────────────────────────────────────────
                if use_tracking and tracked_objects:
                    for tracked in tracked_objects:
                        # Check if object was seen recently enough
                        if ts - tracked.last_seen_ts <= persistence_period:
                            interp_box = tracked.get_interpolated_box(ts, width, height)
                            if interp_box:
                                boxes.append(interp_box)
                
                # ─────────────────────────────────────────────────────────
                # Method 2: Multi-sample aggregation (fallback/supplement)
                # ─────────────────────────────────────────────────────────
                if not boxes or not use_tracking:
                    # Find nearest sample timestamp
                    sample_index = int(ts * sample_fps + 0.5)
                    
                    # Collect from nearby samples
                    for offset in range(-TEMPORAL_WINDOW_FRAMES, TEMPORAL_WINDOW_FRAMES + 1):
                        check_index = sample_index + offset
                        if check_index >= 0:
                            check_ts = check_index / sample_fps
                            key = round(check_ts, 3)
                            detections = sample_lookup.get(key, [])
                            for det in detections:
                                boxes.append(det[0])  # Just the box
                
                # ─────────────────────────────────────────────────────────
                # Method 3: Interpolation between bracketing samples
                # ─────────────────────────────────────────────────────────
                if interpolate_boxes and len(sorted_timestamps) >= 2:
                    prev_ts = None
                    next_ts = None
                    
                    for t in sorted_timestamps:
                        if t <= ts:
                            prev_ts = t
                        if t > ts and next_ts is None:
                            next_ts = t
                            break
                    
                    if prev_ts is not None and next_ts is not None:
                        prev_detections = sample_lookup.get(round(prev_ts, 3), [])
                        next_detections = sample_lookup.get(round(next_ts, 3), [])
                        
                        prev_boxes = [d[0] for d in prev_detections]
                        next_boxes = [d[0] for d in next_detections]
                        
                        t_factor = (ts - prev_ts) / (next_ts - prev_ts) if next_ts != prev_ts else 0.5
                        
                        for prev_box in prev_boxes:
                            match = _find_matching_box(prev_box, next_boxes, frame_diag)
                            if match:
                                interp_box = _interpolate_box(prev_box, match, t_factor)
                                boxes.append(interp_box)
                
                # ─────────────────────────────────────────────────────────
                # Post-processing: deduplicate, merge, expand
                # ─────────────────────────────────────────────────────────
                if boxes:
                    # Remove exact duplicates
                    unique_boxes = list(set(boxes))
                    
                    # Merge overlapping boxes
                    unique_boxes = _merge_overlapping_boxes(unique_boxes, iou_threshold=0.3)
                    
                    # Expand boxes for better coverage
                    if expand_boxes:
                        unique_boxes = [
                            _expand_bbox(
                                box, width, height,
                                expansion_ratio=expansion_ratio,
                                min_expansion_px=BBOX_MIN_EXPANSION_PX,
                            )
                            for box in unique_boxes
                        ]
                    
                    if unique_boxes:
                        frame = blur_boxes_in_frame(
                            frame, 
                            unique_boxes, 
                            ksize=blur_ksize,
                            method="combined",  # Pixelation + blur for best obscuring
                        )

            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()

        # Merge original audio with blurred video
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(temp_video_noaudio),
            "-i", str(video_path),
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:v", "copy",
            "-c:a", "copy",
            "-shortest",
            str(output_video_path),
        ]
        subprocess.run(cmd, check=True)
        
        print(f"[region_blur] Processed {frame_idx} frames, output: {output_video_path}")
