from __future__ import annotations

from typing import List

from google.cloud import vision

from src.aegisai.vision.label_lists import VIOLENCE_LABELS
from src.aegisai.vision.vision_rules import RegionBox


def _build_client(key_path: str) -> vision.ImageAnnotatorClient:
    return vision.ImageAnnotatorClient.from_service_account_file(key_path)


def _load_image_bytes(image_path: str) -> bytes:
    with open(image_path, "rb") as handle:
        return handle.read()


def analyze_localized_objects(
    image_path: str,
    key_path: str = "secrets/aegis-key.json",
) -> List[vision.LocalizedObjectAnnotation]:
    client = _build_client(key_path)
    content = _load_image_bytes(image_path)
    image = vision.Image(content=content)
    response = client.object_localization(image=image)
    return list(response.localized_object_annotations or [])


def offensive_regions_from_objects(
    objects: List[vision.LocalizedObjectAnnotation],
    min_score: float = 0.4,
) -> List[RegionBox]:
    regions: List[RegionBox] = []

    violence_labels = {label.lower() for label in VIOLENCE_LABELS}

    for obj in objects:
        if obj.score < min_score:
            continue

        label = obj.name.strip()
        if label.lower() not in violence_labels:
            continue

        xs = [v.x for v in obj.bounding_poly.normalized_vertices]
        ys = [v.y for v in obj.bounding_poly.normalized_vertices]

        xmin = max(0.0, min(xs))
        xmax = min(1.0, max(xs))
        ymin = max(0.0, min(ys))
        ymax = min(1.0, max(ys))

        if xmax <= xmin or ymax <= ymin:
            continue

        regions.append(
            RegionBox(
                label=label,
                score=float(obj.score),
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
            )
        )

    return regions


def detect_offensive_regions(
    image_path: str,
    key_path: str = "secrets/aegis-key.json",
) -> List[RegionBox]:
    objects = analyze_localized_objects(image_path, key_path=key_path)
    return offensive_regions_from_objects(objects)

