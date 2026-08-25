from sqlalchemy.orm import Session

from achievements.services.achievement_service import achievement_service


class AchievementsFacade:
    def get_achievements_payload(self, db: Session, *, ctx):
        return achievement_service.get_achievements_payload(db, ctx=ctx)

    def get_student_achievements_payload(self, db: Session, student_id: int, *, ctx):
        return achievement_service.get_student_achievements_payload(db, student_id, ctx=ctx)

    async def upload_achievement_media(self, db: Session, *, ctx, achievement_id: int, file, logger=None):
        return await achievement_service.upload_achievement_media(db, ctx=ctx, achievement_id=achievement_id, file=file, logger=logger)

    async def upload_achievement_video(self, db: Session, *, ctx, achievement_id: int, file):
        return await achievement_service.upload_achievement_video(db, ctx=ctx, achievement_id=achievement_id, file=file)

    async def create_achievement_from_form(self, db: Session, *, ctx, title: str, description: str | None, event_date: str | None, place: str | None, assignment_type: str, student_id: int | None, file, logger=None):
        return await achievement_service.create_achievement_from_form(
            db,
            ctx=ctx,
            title=title,
            description=description,
            event_date=event_date,
            place=place,
            assignment_type=assignment_type,
            student_id=student_id,
            file=file,
            logger=logger,
        )

    def assign_achievement(self, db: Session, *, ctx, achievement_id: int, user_id: int):
        return achievement_service.assign_achievement(db, ctx=ctx, achievement_id=achievement_id, user_id=user_id)


achievements_facade = AchievementsFacade()
