"""
Google Vision Object Localization wrapper.

Provides:
- localize_objects_from_path(path): simple helper using image_path
- localize_objects_bytes(bytes, width, height): for FFmpeg pipelines
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

from google.cloud import vision
from PIL import Image as PILImage


@dataclass
class LocalizedObject:
    """
    Represents a detected object in the image.

    name: object label ("Person", "Car", etc.)
    score: confidence 0–1
    bbox: (x_min, y_min, x_max, y_max) in absolute pixel coordinates
    """
    name: str
    score: float
    bbox: Tuple[int, int, int, int]


# ─────────────────────────────────────────────────────────
#  Helper: from image path
# ─────────────────────────────────────────────────────────
def localize_objects_from_path(image_path: str) -> List[LocalizedObject]:
    """
    Run object localization on a file path.
    Automatically loads Google credentials from GOOGLE_APPLICATION_CREDENTIALS.
    """
    client = vision.ImageAnnotatorClient()

    # Read the image bytes
    with open(image_path, "rb") as f:
        content = f.read()

    # Get image width/height via Pillow
    with PILImage.open(image_path) as im:
        width, height = im.size

    return localize_objects_bytes(content, width, height)


# ─────────────────────────────────────────────────────────
#  Main method: from bytes + known width/height
# ─────────────────────────────────────────────────────────
def localize_objects_bytes(
    image_bytes: bytes,
    width: int,
    height: int,
) -> List[LocalizedObject]:
    """
    Run object localization on raw image bytes.
    PERFECT for FFmpeg pipelines where you:
        - already decoded the frame
        - or extracted a JPEG/PNG
        - and know (width, height)

    Example:
        frame_bytes, w, h = extract_frame_via_ffmpeg(...)
        objs = localize_objects_bytes(frame_bytes, w, h)
    """

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    response = client.object_localization(image=image)

    if response.error.message:
        raise RuntimeError(response.error.message)

    results: List[LocalizedObject] = []

    for obj in response.localized_object_annotations:
        # Normalized vertices (float 0..1) → pixel coordinates
        xs = [v.x for v in obj.bounding_poly.normalized_vertices]
        ys = [v.y for v in obj.bounding_poly.normalized_vertices]

        x_min = int(min(xs) * width)
        x_max = int(max(xs) * width)
        y_min = int(min(ys) * height)
        y_max = int(max(ys) * height)

        results.append(
            LocalizedObject(
                name=obj.name,
                score=obj.score,
                bbox=(x_min, y_min, x_max, y_max),
            )
        )

    return results
