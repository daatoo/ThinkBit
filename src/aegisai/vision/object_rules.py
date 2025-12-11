from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, Optional

from src.aegisai.vision.object_localization import LocalizedObject
from src.aegisai.vision.safe_search import Likelihood
from src.aegisai.vision.vision_rules import FrameModerationResult

# ─────────────────────────────────────────────────────────
# Extended keyword lists for comprehensive detection
# ─────────────────────────────────────────────────────────

# Keywords are compared using lowercase substring checks to tolerate
# variations like "Machine gun" vs "gun" or "Breast (anatomy)".
_WEAPON_KEYWORDS: Sequence[str] = (
    # Firearms
    "gun", "firearm", "weapon", "handgun", "pistol", "revolver",
    "rifle", "shotgun", "assault rifle", "machine gun", "submachine",
    "sniper", "ak-47", "ar-15", "m16", "uzi", "glock", "beretta",
    "automatic weapon", "semi-automatic",
    # Explosives
    "grenade", "explosive", "bomb", "rocket", "missile", "bazooka",
    "dynamite", "molotov", "c4", "ied", "landmine", "mortar",
    "rocket launcher", "rpg",
    # Bladed weapons
    "knife", "blade", "dagger", "sword", "machete", "katana",
    "axe", "hatchet", "cleaver", "scalpel", "switchblade",
    "butterfly knife", "stiletto",
    # Other weapons
    "club", "bat", "baton", "taser", "stun gun", "pepper spray",
    "crossbow", "bow", "arrow", "spear", "brass knuckles",
    "nunchaku", "throwing star", "shuriken",
    # Military
    "cannon", "artillery", "tank gun", "turret",
)

_NUDITY_KEYWORDS: Sequence[str] = (
    "breast", "breasts", "nipple", "nipples",
    "torso", "chest", "bare chest", "naked",
    "buttock", "buttocks", "genitalia", "nude",
    "bikini", "lingerie", "underwear",
)

_PERSON_LABELS: Sequence[str] = (
    "person", "man", "woman", "boy", "girl",
    "human", "people", "face", "body", "figure",
    "child", "adult", "male", "female",
)

# Additional dangerous objects that should trigger alerts
_DANGEROUS_OBJECTS: Sequence[str] = (
    "blood", "wound", "injury", "corpse", "dead body",
    "fire", "flames", "smoke", "explosion",
    "drug", "syringe", "needle", "pills",
    "alcohol", "beer", "wine", "liquor", "cigarette",
)


@dataclass(frozen=True)
class ProblematicObject:
    """
    Represents an object that should be blurred.
    
    Attributes:
        bbox: Bounding box (x1, y1, x2, y2) in pixels
        label: Object label from detection
        reason: Why this object is flagged (weapon, nudity, etc.)
        confidence: Detection confidence score
        priority: Blur priority (higher = more important to blur)
    """
    bbox: Tuple[int, int, int, int]
    label: str
    reason: str
    confidence: float = 1.0
    priority: int = 1  # 1=normal, 2=high (weapons), 3=critical


def _matches_any(name: str, keywords: Sequence[str]) -> bool:
    """Check if name contains any of the keywords (case-insensitive)."""
    lowered = name.lower()
    return any(k in lowered for k in keywords)


def _calculate_priority(reason: str, confidence: float) -> int:
    """
    Calculate blur priority based on content type.
    Higher priority = more aggressive blur parameters.
    """
    if reason == "weapon":
        return 3  # Critical - always blur weapons
    elif reason in ("nudity", "adult_person"):
        return 2  # High priority
    elif reason in ("violence_person", "dangerous"):
        return 2
    return 1  # Normal priority


def _merge_overlapping_boxes(
    objects: List[ProblematicObject],
    iou_threshold: float = 0.3,
) -> List[ProblematicObject]:
    """
    Merge significantly overlapping boxes to prevent blur artifacts.
    Keeps the highest priority/confidence detection.
    """
    if len(objects) <= 1:
        return objects
    
    # Sort by priority then confidence
    sorted_objs = sorted(
        objects, 
        key=lambda o: (o.priority, o.confidence), 
        reverse=True
    )
    
    merged: List[ProblematicObject] = []
    used = set()
    
    for i, obj in enumerate(sorted_objs):
        if i in used:
            continue
            
        # Find all overlapping boxes
        group = [obj]
        for j, other in enumerate(sorted_objs[i+1:], start=i+1):
            if j in used:
                continue
            if _boxes_overlap(obj.bbox, other.bbox, iou_threshold):
                group.append(other)
                used.add(j)
        
        # Create merged bounding box
        if len(group) > 1:
            x1 = min(o.bbox[0] for o in group)
            y1 = min(o.bbox[1] for o in group)
            x2 = max(o.bbox[2] for o in group)
            y2 = max(o.bbox[3] for o in group)
            
            merged.append(ProblematicObject(
                bbox=(x1, y1, x2, y2),
                label=obj.label,  # Use highest priority label
                reason=obj.reason,
                confidence=max(o.confidence for o in group),
                priority=max(o.priority for o in group),
            ))
        else:
            merged.append(obj)
        
        used.add(i)
    
    return merged


def _boxes_overlap(
    box1: Tuple[int, int, int, int], 
    box2: Tuple[int, int, int, int], 
    threshold: float = 0.3
) -> bool:
    """Calculate IoU and check if boxes overlap significantly."""
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
    
    return (inter_area / union_area) > threshold


def select_problematic_objects(
    objects: Iterable[LocalizedObject],
    frame_result: Optional[FrameModerationResult],
    weapon_confidence_threshold: float = 0.08,   # Very low - catch all weapons
    nudity_confidence_threshold: float = 0.20,   # Low - safety first
    person_confidence_threshold: float = 0.25,   # Slightly higher for people
    dangerous_confidence_threshold: float = 0.30,
    merge_overlapping: bool = True,
) -> List[ProblematicObject]:
    """
    Keep only objects that correspond to harmful content we want to obscure.

    Detection Categories:
    - Weapons: VERY low confidence threshold (0.08) - always blur suspicious items.
      Better to over-blur than miss a weapon, especially in dark/unclear footage.
    - Nudity indicators: Low threshold (0.20) for anatomical terms.
    - People: Only blurred when frame is flagged as adult/racy/violence.
    - Dangerous objects: Blood, fire, drugs, etc. with moderate threshold.
    
    Args:
        objects: Detected objects from Vision API
        frame_result: Moderation result for the frame (SafeSearch + labels)
        weapon_confidence_threshold: Minimum confidence for weapons (default 0.08)
        nudity_confidence_threshold: Minimum confidence for nudity (default 0.20)
        person_confidence_threshold: Minimum confidence for people (default 0.25)
        dangerous_confidence_threshold: Minimum for dangerous objects (default 0.30)
        merge_overlapping: Whether to merge overlapping boxes (default True)
        
    Returns:
        List of ProblematicObject with blur regions and metadata
    """
    # Parse frame moderation result
    allow_person_blur = False
    violence_detected = False
    
    if frame_result:
        safesearch = frame_result.safesearch or {}
        labels_info = frame_result.labels or {}
        
        adult_score = safesearch.get("adult", Likelihood.UNKNOWN)
        racy_score = safesearch.get("racy", Likelihood.UNKNOWN)
        violence_score = safesearch.get("violence", Likelihood.UNKNOWN)
        
        # Allow person blur if adult/racy content or high violence
        allow_person_blur = (
            adult_score >= Likelihood.LIKELY or 
            racy_score >= Likelihood.LIKELY or
            violence_score >= Likelihood.LIKELY
        )
        violence_detected = bool(labels_info.get("violence_detected"))
        
        # Also blur people if violence labels detected
        if violence_detected:
            allow_person_blur = True

    keep: List[ProblematicObject] = []

    for obj in objects:
        name = obj.name or ""
        score = obj.score
        reason: Optional[str] = None
        threshold_to_use = 1.0  # Will be set based on category

        # ─────────────────────────────────────────────────────────
        # Category 1: WEAPONS (highest priority, lowest threshold)
        # ─────────────────────────────────────────────────────────
        if _matches_any(name, _WEAPON_KEYWORDS):
            threshold_to_use = weapon_confidence_threshold
            if score >= threshold_to_use:
                reason = "weapon"
                
        # ─────────────────────────────────────────────────────────
        # Category 2: NUDITY
        # ─────────────────────────────────────────────────────────
        elif _matches_any(name, _NUDITY_KEYWORDS):
            threshold_to_use = nudity_confidence_threshold
            if score >= threshold_to_use:
                reason = "nudity"
                
        # ─────────────────────────────────────────────────────────
        # Category 3: PEOPLE (only in flagged content)
        # ─────────────────────────────────────────────────────────
        elif _matches_any(name, _PERSON_LABELS):
            threshold_to_use = person_confidence_threshold
            if score >= threshold_to_use:
                if allow_person_blur:
                    if violence_detected:
                        reason = "violence_person"
                    else:
                        reason = "adult_person"
                        
        # ─────────────────────────────────────────────────────────
        # Category 4: DANGEROUS OBJECTS
        # ─────────────────────────────────────────────────────────
        elif _matches_any(name, _DANGEROUS_OBJECTS):
            threshold_to_use = dangerous_confidence_threshold
            if score >= threshold_to_use:
                reason = "dangerous"

        # Add to results if flagged
        if reason:
            priority = _calculate_priority(reason, score)
            keep.append(ProblematicObject(
                bbox=obj.bbox, 
                label=name, 
                reason=reason,
                confidence=score,
                priority=priority,
            ))

    # Optionally merge overlapping boxes
    if merge_overlapping and len(keep) > 1:
        keep = _merge_overlapping_boxes(keep)

    return keep


def get_all_blur_boxes(
    problematic_objects: List[ProblematicObject],
) -> List[Tuple[int, int, int, int]]:
    """
    Extract just the bounding boxes from problematic objects.
    Utility function for backward compatibility.
    """
    return [obj.bbox for obj in problematic_objects]

