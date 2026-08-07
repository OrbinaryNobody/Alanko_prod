import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from achievements.dtos.achievement_dto import AchievementPayload


def test_achievement_payload_serializes_fields():
    payload = AchievementPayload(id=1, title="Award", description="Desc", event_date="2024-01-01", place="1st", is_collective=False)
    assert payload.to_dict()["title"] == "Award"
    assert payload.to_dict()["is_collective"] is False
