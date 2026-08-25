from sqlalchemy.orm import Session

from public.services.public_service import public_service


class PublicFacade:
    def get_public_leaderboard(self, db: Session):
        return public_service.get_public_leaderboard(db)

    def get_public_achievement_videos(self, db: Session, *, limit: int = 20, offset: int = 0):
        return public_service.get_public_achievement_videos(db, limit=limit, offset=offset)

    def get_student_videos(self, db: Session, student_id: int, *, ctx):
        return public_service.get_student_videos(db, student_id=student_id, ctx=ctx)


public_facade = PublicFacade()
