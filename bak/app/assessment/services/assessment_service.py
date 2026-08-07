from sqlalchemy.orm import Session

from assessment.dtos.assessment_dto import AssessmentPayload
from assessment.policies.assessment_policy import AssessmentPolicy
from assessment.repositories.assessment_repository import assessment_repository
from core.access import AccessContext
from core.exceptions import NotFoundError, PermissionDenied


class AssessmentService:
    def get_assessment_payload(self, db: Session, *, ctx: AccessContext, student_id: int, task_id: int):
        try:
            AssessmentPolicy.require_view_assessment(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to assessment") from exc

        student = assessment_repository.get_student(db, student_id=student_id)
        if not student:
            raise NotFoundError("Student not found")

        task = assessment_repository.get_task(db, task_id=task_id)
        if not task:
            raise NotFoundError("Task not found")

        min_difficulty = max(1, task.difficulty - 1)
        max_difficulty = task.difficulty + 1

        student_similar_tasks = assessment_repository.list_similar_student_tasks(
            db,
            student_id=student_id,
            min_difficulty=min_difficulty,
            max_difficulty=max_difficulty,
        )
        student_scores = [st.score for st in student_similar_tasks]
        student_avg_score = sum(student_scores) / len(student_scores) if student_scores else 0

        all_task_scores = assessment_repository.list_completed_task_scores(db, task_id=task_id)
        all_scores = [st.score for st in all_task_scores]
        class_avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        if class_avg_score == 0:
            readiness_level = "unknown"
            indicator_color = "gray"
        elif student_avg_score >= class_avg_score:
            readiness_level = "good"
            indicator_color = "green"
        elif student_avg_score >= class_avg_score * 0.7:
            readiness_level = "medium"
            indicator_color = "yellow"
        else:
            readiness_level = "poor"
            indicator_color = "red"

        current_student_task = assessment_repository.get_current_student_task(db, student_id=student_id, task_id=task_id)

        return AssessmentPayload(
            student_id=student_id,
            task_id=task_id,
            task={
                "title": task.title,
                "difficulty": task.difficulty,
                "max_score": task.max_score,
            },
            student_performance={
                "average_score_similar": round(student_avg_score, 2),
                "tasks_completed_similar": len(student_scores),
                "best_score": max(student_scores) if student_scores else 0,
                "worst_score": min(student_scores) if student_scores else 0,
            },
            class_average=round(class_avg_score, 2),
            students_completed_task=len(all_scores),
            assessment={
                "readiness_level": readiness_level,
                "indicator_color": indicator_color,
                "recommendation": self._get_recommendation_text(readiness_level),
            },
            current_status={
                "status": current_student_task.status if current_student_task else "not_assigned",
                "score": current_student_task.score if current_student_task else None,
                "comment": current_student_task.comment if current_student_task else None,
            },
        ).to_dict()

    def _get_recommendation_text(self, readiness_level: str) -> str:
        recommendations = {
            "good": "✓ Студент хорошо подготовлен к этой задаче",
            "medium": "○ Студент средне подготовлен, может потребоваться помощь",
            "poor": "! Студент слабо подготовлен, рекомендуется дополнительная поддержка",
            "unknown": "? Недостаточно данных для оценки",
        }
        return recommendations.get(readiness_level, "?")


assessment_service = AssessmentService()
