"""
Google Vision Object Localization wrapper with enhanced detection.

Provides:
- localize_objects_from_path(path): simple helper using image_path
- localize_objects_bytes(bytes, width, height): for FFmpeg pipelines
- Enhanced detection combining object localization + label detection for better coverage
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
import hashlib

from google.cloud import vision
from PIL import Image as PILImage


@dataclass
class LocalizedObject:
    """
    Represents a detected object in the image.

    name: object label ("Person", "Car", etc.)
    score: confidence 0–1
    bbox: (x_min, y_min, x_max, y_max) in absolute pixel coordinates
    mid: optional Machine-generated identifier for tracking
    """
    name: str
    score: float
    bbox: Tuple[int, int, int, int]
    mid: Optional[str] = None  # Machine-generated ID for potential tracking

    def area(self) -> int:
        """Calculate bounding box area for size-based filtering."""
        x1, y1, x2, y2 = self.bbox
        return max(0, (x2 - x1) * (y2 - y1))
    
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)


# Minimum confidence thresholds (lower = more aggressive detection)
DEFAULT_MIN_CONFIDENCE = 0.10  # Very low to catch more objects
WEAPON_MIN_CONFIDENCE = 0.05   # Extra low for weapons - better safe than sorry

# Labels that should trigger full-frame analysis for potential missed objects
HIGH_PRIORITY_LABELS: Set[str] = {
    "gun", "firearm", "weapon", "knife", "blade", "sword", 
    "person", "people", "man", "woman", "human"
}


def _compute_object_hash(obj: LocalizedObject) -> str:
    """Generate a hash for deduplication based on position and label."""
    x1, y1, x2, y2 = obj.bbox
    return hashlib.md5(
        f"{obj.name}:{x1//20}:{y1//20}:{x2//20}:{y2//20}".encode()
    ).hexdigest()[:8]


def _boxes_overlap(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int], threshold: float = 0.5) -> bool:
    """Check if two boxes overlap significantly (IoU > threshold)."""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Intersection
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    
    if xi1 >= xi2 or yi1 >= yi2:
        return False
    
    inter_area = (xi2 - xi1) * (yi2 - yi1)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    
    if union_area <= 0:
        return False
    
    iou = inter_area / union_area
    return iou > threshold


def _deduplicate_objects(objects: List[LocalizedObject]) -> List[LocalizedObject]:
    """Remove duplicate/overlapping detections, keeping highest confidence."""
    if not objects:
        return []
    
    # Sort by confidence (highest first)
    sorted_objs = sorted(objects, key=lambda o: o.score, reverse=True)
    kept: List[LocalizedObject] = []
    
    for obj in sorted_objs:
        # Check if this object significantly overlaps with any kept object
        is_duplicate = False
        for kept_obj in kept:
            if _boxes_overlap(obj.bbox, kept_obj.bbox, threshold=0.4):
                # Same area - keep the higher confidence one (already in kept)
                is_duplicate = True
                break
        
        if not is_duplicate:
            kept.append(obj)
    
    return kept


# ─────────────────────────────────────────────────────────
#  Helper: from image path
# ─────────────────────────────────────────────────────────
def localize_objects_from_path(
    image_path: str,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    include_labels: bool = True,
) -> List[LocalizedObject]:
    """
    Run enhanced object localization on a file path.
    
    Args:
        image_path: Path to the image file
        min_confidence: Minimum confidence threshold (default very low for safety)
        include_labels: Also run label detection for additional context
        
    Returns:
        List of LocalizedObject with detected objects and their bounding boxes
    """
    # Read the image bytes
    with open(image_path, "rb") as f:
        content = f.read()

    # Get image width/height via Pillow
    with PILImage.open(image_path) as im:
        width, height = im.size

    return localize_objects_bytes(
        content, width, height,
        min_confidence=min_confidence,
        include_labels=include_labels
    )


# ─────────────────────────────────────────────────────────
#  Main method: from bytes + known width/height
# ─────────────────────────────────────────────────────────
def localize_objects_bytes(
    image_bytes: bytes,
    width: int,
    height: int,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    include_labels: bool = True,
) -> List[LocalizedObject]:
    """
    Run enhanced object localization on raw image bytes.
    
    Combines multiple detection strategies:
    1. Primary object localization API (bounding boxes)
    2. Label detection for additional context (helps identify missed weapons)
    
    Args:
        image_bytes: Raw image bytes (JPEG/PNG)
        width: Image width in pixels
        height: Image height in pixels
        min_confidence: Minimum confidence to include object
        include_labels: Also analyze with label detection API
        
    Returns:
        List of LocalizedObject with comprehensive detections
    """
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    
    results: List[LocalizedObject] = []
    
    # ─────────────────────────────────────────────────────────
    # 1. Primary: Object Localization API
    # ─────────────────────────────────────────────────────────
    try:
        response = client.object_localization(image=image)
        
        if response.error.message:
            print(f"[object_localization] API error: {response.error.message}")
        else:
            for obj in response.localized_object_annotations:
                # Skip very low confidence detections
                if obj.score < min_confidence:
                    continue
                    
                # Normalized vertices (float 0..1) → pixel coordinates
                vertices = obj.bounding_poly.normalized_vertices
                if len(vertices) < 4:
                    continue
                    
                xs = [v.x for v in vertices]
                ys = [v.y for v in vertices]

                x_min = int(min(xs) * width)
                x_max = int(max(xs) * width)
                y_min = int(min(ys) * height)
                y_max = int(max(ys) * height)
                
                # Ensure valid box dimensions
                if x_max <= x_min or y_max <= y_min:
                    continue

                results.append(
                    LocalizedObject(
                        name=obj.name,
                        score=obj.score,
                        bbox=(x_min, y_min, x_max, y_max),
                        mid=obj.mid if hasattr(obj, 'mid') else None,
                    )
                )
    except Exception as e:
        print(f"[object_localization] Object localization failed: {e}")
    
    # ─────────────────────────────────────────────────────────
    # 2. Secondary: Label Detection for additional context
    #    (doesn't provide boxes but helps identify content types)
    # ─────────────────────────────────────────────────────────
    if include_labels:
        try:
            label_response = client.label_detection(image=image)
            
            if not label_response.error.message:
                for label in label_response.label_annotations:
                    label_name = label.description.lower()
                    
                    # If we detect a high-priority label but have no localized objects
                    # of that type, we may have missed something - flag for attention
                    if any(hp in label_name for hp in HIGH_PRIORITY_LABELS):
                        # Check if we already have this type detected
                        has_similar = any(
                            hp in obj.name.lower() 
                            for obj in results 
                            for hp in HIGH_PRIORITY_LABELS 
                            if hp in label_name
                        )
                        
                        # If label detected but no localized object, log for debugging
                        if not has_similar and label.score >= 0.5:
                            print(f"[object_localization] Label '{label.description}' detected "
                                  f"(score={label.score:.2f}) but no localized object found")
                            
        except Exception as e:
            print(f"[object_localization] Label detection auxiliary check failed: {e}")
    
    # ─────────────────────────────────────────────────────────
    # 3. Deduplicate overlapping detections
    # ─────────────────────────────────────────────────────────
    results = _deduplicate_objects(results)
    
    return results


def localize_objects_batch(
    image_paths: List[str],
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> List[Tuple[str, List[LocalizedObject]]]:
    """
    Batch process multiple images for efficiency.
    
    Args:
        image_paths: List of image file paths
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of (path, objects) tuples
    """
    results = []
    for path in image_paths:
        try:
            objects = localize_objects_from_path(path, min_confidence=min_confidence)
            results.append((path, objects))
        except Exception as e:
            print(f"[object_localization] Failed to process {path}: {e}")
            results.append((path, []))
    return results
