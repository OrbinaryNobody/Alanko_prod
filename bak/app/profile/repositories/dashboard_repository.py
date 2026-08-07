from sqlalchemy.orm import Session, joinedload

from models.domains.achievements import Achievement, UserAchievement
from models.domains.auth import User
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia


class DashboardRepository:
    def get_profile(self, db: Session, *, user_id: int) -> StudentProfile | None:
        return db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    def get_user(self, db: Session, *, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def get_tasks(self, db: Session, *, user_id: int) -> list[StudentTask]:
        return db.query(StudentTask).filter(StudentTask.student_id == user_id).all()

    def get_videos(self, db: Session, *, user_id: int) -> list[TaskMedia]:
        return db.query(TaskMedia).join(StudentTask).filter(StudentTask.student_id == user_id).all()

    def get_user_achievements(self, db: Session, *, user_id: int) -> list[UserAchievement]:
        return (
            db.query(UserAchievement)
            .options(joinedload(UserAchievement.achievement))
            .filter(UserAchievement.user_id == user_id)
            .all()
        )

    def get_collective_achievements(self, db: Session) -> list[Achievement]:
        return db.query(Achievement).filter(Achievement.is_collective == True).all()

    def get_history(self, db: Session, *, user_id: int) -> list[RatingsHistory]:
        return (
            db.query(RatingsHistory)
            .filter(RatingsHistory.student_id == user_id)
            .order_by(RatingsHistory.created_at.desc())
            .all()
        )

    def get_leaderboard_profiles(self, db: Session) -> list[StudentProfile]:
        return db.query(StudentProfile).join(User).order_by(StudentProfile.rating_points.desc()).all()

    def get_student_tasks(self, db: Session, *, user_id: int) -> list[StudentTask]:
        return (
            db.query(StudentTask)
            .options(joinedload(StudentTask.task).joinedload(Task.category), joinedload(StudentTask.media))
            .filter(StudentTask.student_id == user_id)
            .all()
        )


dashboard_repository = DashboardRepository()
