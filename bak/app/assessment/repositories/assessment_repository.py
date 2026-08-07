from sqlalchemy.orm import Session

from models.domains.auth import User
from models.domains.student import StudentTask, Task


class AssessmentRepository:
    def get_student(self, db: Session, *, student_id: int) -> User | None:
        return db.query(User).filter(User.id == student_id).first()

    def get_task(self, db: Session, *, task_id: int) -> Task | None:
        return db.query(Task).filter(Task.id == task_id).first()

    def list_similar_student_tasks(self, db: Session, *, student_id: int, min_difficulty: int, max_difficulty: int) -> list[StudentTask]:
        return (
            db.query(StudentTask)
            .join(Task, StudentTask.task_id == Task.id)
            .filter(
                StudentTask.student_id == student_id,
                Task.difficulty.between(min_difficulty, max_difficulty),
                StudentTask.score > 0,
            )
            .all()
        )

    def list_completed_task_scores(self, db: Session, *, task_id: int) -> list[StudentTask]:
        return db.query(StudentTask).filter(StudentTask.task_id == task_id, StudentTask.score > 0).all()

    def get_current_student_task(self, db: Session, *, student_id: int, task_id: int) -> StudentTask | None:
        return db.query(StudentTask).filter(StudentTask.student_id == student_id, StudentTask.task_id == task_id).first()


assessment_repository = AssessmentRepository()
