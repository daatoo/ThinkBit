from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.aegisai.vision.object_localization import LocalizedObject
from src.aegisai.vision.safe_search import Likelihood
from src.aegisai.vision.vision_rules import FrameModerationResult

# Keywords are compared using lowercase substring checks to tolerate
# variations like "Machine gun" vs "gun" or "Breast (anatomy)".
_WEAPON_KEYWORDS: Sequence[str] = (
    "gun",
    "firearm",
    "weapon",
    "handgun",
    "pistol",
    "revolver",
    "rifle",
    "shotgun",
    "assault rifle",
    "machine gun",
    "submachine",
    "sniper",
    "ak-47",
    "ar-15",
    "grenade",
    "explosive",
    "bomb",
    "rocket",
    "missile",
    "bazooka",
    "knife",
    "blade",
    "dagger",
    "sword",
    "machete",
    "axe",
    "hatchet",
    "club",
    "bat",
    "taser",
    "crossbow",
    "bow",
    "arrow",
)

_NUDITY_KEYWORDS: Sequence[str] = (
    "breast",
    "breasts",
    "nipple",
    "nipples",
    "torso",
    "chest",
)

_PERSON_LABELS: Sequence[str] = (
    "person",
    "man",
    "woman",
    "boy",
    "girl",
)


@dataclass(frozen=True)
class ProblematicObject:
    bbox: tuple[int, int, int, int]
    label: str
    reason: str


def _matches_any(name: str, keywords: Sequence[str]) -> bool:
    lowered = name.lower()
    return any(k in lowered for k in keywords)


def select_problematic_objects(
    objects: Iterable[LocalizedObject],
    frame_result: FrameModerationResult | None,
) -> List[ProblematicObject]:
    """
    Keep only objects that correspond to harmful content we want to obscure.

    - Weapons: blur immediately (guns, knives, explosives, etc.).
    - Nudity indicators: blur when labels include anatomical terms (breast,
      nipple, torso, chest).
    - People: only blurred when the frame is already flagged as adult/racy
      (SafeSearch) or violence detected; this keeps clean/person-only scenes
      untouched.
    """
    if frame_result:
        safesearch = frame_result.safesearch or {}
        labels_info = frame_result.labels or {}
        adult_score = safesearch.get("adult", Likelihood.UNKNOWN)
        racy_score = safesearch.get("racy", Likelihood.UNKNOWN)
        allow_person = (
            adult_score >= Likelihood.LIKELY or racy_score >= Likelihood.LIKELY
        )
        violence_detected = bool(labels_info.get("violence_detected"))
    else:
        allow_person = False
        violence_detected = False

    keep: List[ProblematicObject] = []

    for obj in objects:
        name = obj.name or ""
        reason: str | None = None

        if _matches_any(name, _WEAPON_KEYWORDS):
            reason = "weapon"
        elif _matches_any(name, _NUDITY_KEYWORDS):
            reason = "nudity"
        elif allow_person and name.lower() in _PERSON_LABELS:
            reason = "adult_person"
        elif violence_detected and name.lower() in _PERSON_LABELS:
            reason = "violence_person"

        if reason:
            keep.append(ProblematicObject(bbox=obj.bbox, label=name, reason=reason))

    return keep

