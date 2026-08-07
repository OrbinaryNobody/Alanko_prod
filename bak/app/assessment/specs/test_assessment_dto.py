import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from assessment.dtos.assessment_dto import AssessmentPayload


def test_assessment_payload_serializes_fields():
    payload = AssessmentPayload(
        student_id=1,
        task_id=2,
        task={"title": "Task", "difficulty": 2, "max_score": 10},
        student_performance={"average_score_similar": 8.5, "tasks_completed_similar": 3, "best_score": 10, "worst_score": 5},
        class_average=7.5,
        students_completed_task=4,
        assessment={"readiness_level": "good", "indicator_color": "green", "recommendation": "ok"},
        current_status={"status": "done", "score": 8, "comment": None},
    )
    data = payload.to_dict()
    assert data["student_id"] == 1
    assert data["assessment"]["readiness_level"] == "good"
