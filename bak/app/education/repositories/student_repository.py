from sqlalchemy.orm import Session, joinedload

from models.domains.auth import Role, User
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia


class StudentRepository:
    def get_student_by_id(self, db: Session, *, student_id: int) -> User | None:
        return db.query(User).filter(User.id == student_id).first()

    def get_students(self, db: Session) -> list[User]:
        return (
            db.query(User)
            .join(User.roles)
            .join(Role)
            .filter(Role.name == "student")
            .all()
        )

    def get_students_for_teacher(self, db: Session) -> list[User]:
        return (
            db.query(User)
            .filter(User.student_profile.has())
            .options(
                joinedload(User.student_profile),
                joinedload(User.student_tasks).joinedload(StudentTask.task).joinedload(Task.category),
                joinedload(User.student_tasks).joinedload(StudentTask.media),
            )
            .all()
        )

    def get_last_rating_history(self, db: Session, *, student_id: int) -> RatingsHistory | None:
        return (
            db.query(RatingsHistory)
            .filter(RatingsHistory.student_id == student_id)
            .order_by(RatingsHistory.created_at.desc())
            .first()
        )

    def create_media(self, db: Session, *, student_task_id: int, uploaded_by: int, video_url: str) -> TaskMedia:
        media = TaskMedia(student_task_id=student_task_id, uploaded_by=uploaded_by, video_url=video_url)
        db.add(media)
        db.flush()
        db.refresh(media)
        return media

    def create_rating_history(self, db: Session, *, student_id: int, points_change: int, reason: str) -> RatingsHistory:
        history = RatingsHistory(student_id=student_id, points_change=points_change, reason=reason)
        db.add(history)
        db.flush()
        db.refresh(history)
        return history


student_repository = StudentRepository()
