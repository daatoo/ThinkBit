## `src/aegisai/vision` – Image analysis & frame-level moderation

This package wraps **Google Cloud Vision** (SafeSearch, labels, object localization) and converts raw detections into per-frame “block / ok” decisions and unsafe time intervals for video.

Files:

- `label_detection.py`
- `label_lists.py`
- `object_localization.py`
- `safe_search.py`
- `vision_rules.py`

Requires: Google Cloud Vision credentials via `GOOGLE_APPLICATION_CREDENTIALS` (same service account as the rest of Aegis).

---

### `label_detection.py`

Simple wrapper around Vision **label detection**.

- `analyze_labels(image_path: str) -> list[dict]`
  - Creates `vision.ImageAnnotatorClient()`.
  - Reads image bytes from `image_path`.
  - Calls `client.label_detection(image=image)`.
  - Returns a Python list of:
    ```python
    {
      "description": label.description,  # e.g. "Gun", "Blood"
      "score": label.score,              # float 0..1
    }
    ```
  - Used by `classify_labels` for violence detection.

---

### `label_lists.py`

Violence-related label vocabulary for post-processing Vision labels.

- `VIOLENCE_LABELS: set[str]`
  - Large curated set of strings representing:
    - **Weapons** (Gun, Rifle, Knife, Sword, Grenade, Rocket launcher, …)
    - **Human violence** (Fight, Assault, Shooting, Stabbing, Execution, Riot, …)
    - **Blood / gore** (Blood, Gore, Injury, Deep cut, Dead body, Corpse, …)
    - **War / military** (War, Battle, Explosion, Drone strike, Tank, Soldier, …)
    - **Dangerous situations** (Car crash, Wildfire, Burning building, …)
    - **Crime / illegal** (Robbery, Gang member, Police chase, Vandalism, …)
    - **Disturbing / sensitive** (Animal abuse, Hunting kill, Surgery, Amputation, …)
  - Used verbatim in `classify_labels`: any Vision label whose `description` is in this set and passes a score threshold may trigger a block.

---

### `object_localization.py`

Wrapper around Vision **object localization** for detecting objects and their pixel bounding boxes.

- `@dataclass LocalizedObject`
  - `name: str` – object label (e.g. `"Person"`, `"Car"`).
  - `score: float` – confidence ∈ [0,1].
  - `bbox: tuple[int,int,int,int]` – `(x_min, y_min, x_max, y_max)` in **absolute pixels**.

- `localize_objects_from_path(image_path: str) -> list[LocalizedObject]`
  - Creates `vision.ImageAnnotatorClient()`.
  - Reads image bytes from file.
  - Uses Pillow to get `(width, height)` of the image.
  - Delegates to `localize_objects_bytes(content, width, height)`.

- `localize_objects_bytes(image_bytes: bytes, width: int, height: int) -> list[LocalizedObject]`
  - Creates `vision.ImageAnnotatorClient()` and `vision.Image(content=...)`.
  - Calls `client.object_localization(image=image)`.
  - On `response.error.message` (non-empty), raises `RuntimeError`.
  - For each `response.localized_object_annotations` item:
    - Extracts normalized vertices (`0..1`) from `obj.bounding_poly.normalized_vertices`.
    - Converts to pixel coordinates:
      ```python
      x_min = int(min(xs) * width)
      x_max = int(max(xs) * width)
      y_min = int(min(ys) * height)
      y_max = int(max(ys) * height)
      ```
    - Appends `LocalizedObject(name=obj.name, score=obj.score, bbox=(x_min, y_min, x_max, y_max))`.
  - Returns full list of detected objects; used later to blur moving objects.

---

### `safe_search.py`

Wrapper around Vision **SafeSearch** + top-level per-frame moderation entrypoint.

#### SafeSearch types

- `class Likelihood(IntEnum)`
  - `UNKNOWN = 0`
  - `VERY_UNLIKELY = 1`
  - `UNLIKELY = 2`
  - `POSSIBLE = 3`
  - `LIKELY = 4`
  - `VERY_LIKELY = 5`

- `@dataclass SafeSearchResult`
  - `adult: Likelihood`
  - `violence: Likelihood`
  - `racy: Likelihood`
  - `medical: Likelihood`
  - `spoof: Likelihood`

#### Core SafeSearch API

- `analyze_safesearch(image_path: str) -> SafeSearchResult`
  - Creates `vision.ImageAnnotatorClient()`.
  - Reads image bytes from file.
  - Calls `client.safe_search_detection(image=image)`.
  - Reads `safe = response.safe_search_annotation`.
  - Returns `SafeSearchResult` where each field is wrapped in `Likelihood(...)`.

#### Frame-level moderation (used by video module)

Imports:

- `analyze_labels` (from `label_detection`)
- `classify_safesearch`, `classify_labels`, `combine_frame_decision`, `FrameModerationResult` (from `vision_rules`)

Function:

- `analyze_frame_moderation(image_path: str, timestamp: float) -> FrameModerationResult`
  1. Calls `analyze_safesearch(image_path)` → `SafeSearchResult`.
  2. Calls `classify_safesearch(ss_result)` → `ss_info: dict` with `block` flag.
  3. Calls `analyze_labels(image_path)` → list of `{description, score}`.
  4. Calls `classify_labels(labels)` → `labels_info: dict` with `block` flag.
  5. Calls `combine_frame_decision(timestamp, ss_info, labels_info)` and returns the resulting `FrameModerationResult`.
  - This is the **single entrypoint** the video pipeline uses for per-frame decisions.

---

### `vision_rules.py`

Rules for turning raw Vision output into **block / ok** flags and time intervals.

Imports:

- `VIOLENCE_LABELS` from `.label_lists`
- `Likelihood` from `.safe_search`

#### SafeSearch rules

- `classify_safesearch(result: SafeSearchResult) -> dict`
  - Extracts `.adult`, `.violence`, `.racy` as integer `value`s.
  - Computes:
    ```python
    block = (
        adult    >= Likelihood.LIKELY or
        violence >= Likelihood.LIKELY or
        racy     >= Likelihood.VERY_LIKELY
    )
    ```
  - Returns:
    ```python
    {
      "adult": adult,
      "violence": violence,
      "racy": racy,
      "block": block,
    }
    ```

#### Label-based violence rules

- `classify_labels(labels: list[dict], threshold: float = 0.60) -> dict`
  - `labels` is the output from `analyze_labels`.
  - Iterates through:
    ```python
    desc = item["description"]
    score = item["score"]
    ```
  - If `desc in VIOLENCE_LABELS` **and** `score >= threshold`, returns:
    ```python
    {
      "violence_detected": True,
      "label": desc,
      "score": score,
      "block": True,
    }
    ```
  - If no such label found, returns:
    ```python
    {
      "violence_detected": False,
      "block": False,
    }
    ```

#### Frame decision + interval construction

- `@dataclass FrameModerationResult`
  - `timestamp: float` – sampled frame time (seconds).
  - `safesearch: dict` – output of `classify_safesearch`.
  - `labels: dict` – output of `classify_labels`.
  - `block: bool` – final per-frame unsafe flag.

- `combine_frame_decision(timestamp: float, safesearch_info: dict, labels_info: dict) -> FrameModerationResult`
  - Current logic:
    ```python
    block = bool(safesearch_info.get("block") or labels_info.get("block"))
    ```
  - Returns `FrameModerationResult(timestamp, safesearch_info, labels_info, block)`.

- `intervals_from_frames(frames: list[FrameModerationResult], frame_step: float) -> list[tuple[float, float]]`
  - Converts per-frame decisions into continuous unsafe intervals.
  - `frame_step` = seconds between sampled frames (e.g. `1 / sample_fps`).
  - Iterates frames in order, maintaining `current_start`:
    - When `f.block` switches from `False → True`, sets `current_start = f.timestamp`.
    - When `True → False`, appends interval `(current_start, f.timestamp + frame_step)` and resets `current_start = None`.
  - After the loop, if `current_start` is still active and there were frames, closes the final interval using `last_ts = frames[-1].timestamp`:
    - appends `(current_start, last_ts + frame_step)`.
  - Returns a list of `(start, end)` unsafe intervals used by the video pipeline.

---
