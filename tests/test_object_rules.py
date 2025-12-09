from src.aegisai.vision.object_localization import LocalizedObject
from src.aegisai.vision.object_rules import select_problematic_objects
from src.aegisai.vision.safe_search import Likelihood
from src.aegisai.vision.vision_rules import FrameModerationResult


def _frame_result(
    adult: Likelihood = Likelihood.UNKNOWN,
    racy: Likelihood = Likelihood.UNKNOWN,
    violence: bool = False,
) -> FrameModerationResult:
    return FrameModerationResult(
        timestamp=0.0,
        safesearch={
            "adult": adult,
            "violence": Likelihood.UNKNOWN,
            "racy": racy,
            "block": False,
        },
        labels={
            "violence_detected": violence,
            "block": violence,
        },
        block=False,
    )


def test_weapon_is_always_flagged():
    objs = [LocalizedObject(name="Gun", score=0.9, bbox=(0, 0, 10, 10))]
    selected = select_problematic_objects(objs, frame_result=None)
    assert len(selected) == 1
    assert selected[0].reason == "weapon"


def test_person_not_flagged_when_safe():
    objs = [LocalizedObject(name="Person", score=0.9, bbox=(0, 0, 10, 10))]
    selected = select_problematic_objects(objs, frame_result=_frame_result())
    assert selected == []


def test_person_flagged_when_adult():
    objs = [LocalizedObject(name="Person", score=0.9, bbox=(0, 0, 10, 10))]
    selected = select_problematic_objects(
        objs, frame_result=_frame_result(adult=Likelihood.LIKELY)
    )
    assert len(selected) == 1
    assert selected[0].reason == "adult_person"


def test_nudity_keywords_flagged():
    objs = [LocalizedObject(name="Breast", score=0.8, bbox=(5, 5, 15, 15))]
    selected = select_problematic_objects(objs, frame_result=None)
    assert len(selected) == 1
    assert selected[0].reason == "nudity"

