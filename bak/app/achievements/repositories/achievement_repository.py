from sqlalchemy.orm import Session

from models.domains.achievements import Achievement, UserAchievement


class AchievementRepository:
    def list_all(self, db: Session) -> list[Achievement]:
        return db.query(Achievement).all()

    def list_for_student(self, db: Session, *, student_id: int) -> list[UserAchievement]:
        return db.query(UserAchievement).filter(UserAchievement.user_id == student_id).all()

    def get_by_id(self, db: Session, *, achievement_id: int) -> Achievement | None:
        return db.query(Achievement).filter(Achievement.id == achievement_id).first()

    def get_assignment(self, db: Session, *, user_id: int, achievement_id: int) -> UserAchievement | None:
        return db.query(UserAchievement).filter(UserAchievement.user_id == user_id, UserAchievement.achievement_id == achievement_id).first()

    def create(self, db: Session, achievement: Achievement) -> Achievement:
        db.add(achievement)
        db.flush()
        db.refresh(achievement)
        return achievement

    def create_assignment(self, db: Session, assignment: UserAchievement) -> UserAchievement:
        db.add(assignment)
        db.flush()
        db.refresh(assignment)
        return assignment


achievement_repository = AchievementRepository()
