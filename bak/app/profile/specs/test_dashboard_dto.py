import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from profile.dtos.dashboard_dto import DashboardPayload, StudentTaskPayload


def test_dashboard_payload_serializes_expected_fields():
    payload = DashboardPayload(user_id=1, rating=42, tasks=3, place=7, total_students=20)
    data = payload.to_dict()
    assert data["rating"] == 42
    assert data["tasks"] == 3


def test_student_task_payload_serializes_expected_fields():
    payload = StudentTaskPayload(student_task_id=10, task_id=2, title="Task", status="done", score=5, max_score=10)
    assert payload.to_dict()["status"] == "done"
