from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AssessmentPayload:
    student_id: int
    task_id: int
    task: dict[str, Any]
    student_performance: dict[str, Any]
    class_average: float
    students_completed_task: int
    assessment: dict[str, Any]
    current_status: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "task_id": self.task_id,
            "task": self.task,
            "student_performance": self.student_performance,
            "class_average": self.class_average,
            "students_completed_task": self.students_completed_task,
            "assessment": self.assessment,
            "current_status": self.current_status,
        }
