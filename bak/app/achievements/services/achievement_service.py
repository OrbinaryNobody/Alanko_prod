from datetime import datetime
from sqlalchemy.orm import Session

from achievements.dtos.achievement_dto import AchievementPayload
from achievements.policies.achievement_policy import AchievementPolicy
from achievements.repositories.achievement_repository import achievement_repository
from accounts.facade import accounts_facade
from core.access import AccessContext
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from db.minio_client import BUCKET_NAMES
from models.domains.achievements import Achievement, UserAchievement
from models.domains.auth import User
from models.domains.education import GroupEnrollment, GroupMember
from infrastructure.storage.file_service import file_service
from shared.unit_of_work import UnitOfWork


class AchievementService:
    def _can_view_student(self, db: Session, *, ctx: AccessContext, student_id: int) -> bool:
        if ctx.is_admin or ctx.user_id == student_id or ctx.has_role("secretary"):
            return True
        return (
            db.query(GroupEnrollment)
            .join(GroupMember, GroupMember.group_id == GroupEnrollment.group_id)
            .filter(
                GroupEnrollment.student_id == student_id,
                GroupEnrollment.status == "active",
                GroupMember.user_id == ctx.user_id,
            )
            .first()
            is not None
        )

    def get_achievements_payload(self, db: Session, *, ctx: AccessContext):
        try:
            AchievementPolicy.require_view_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to achievements") from exc

        achievements = achievement_repository.list_all(db)
        result = []

        for achievement in achievements:
            assignment = achievement.users[0] if achievement.users else None
            student = assignment.user if assignment else None
            profile = student.student_profile if student else None
            image_key = profile.image_url if profile and profile.image_url else student.image_url if student else None
            file_url = None
            if achievement.certificate_url:
                file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

            video_url = None
            if achievement.video_url and achievement.is_public:
                video_url = file_service.get_file_url(achievement.video_url, BUCKET_NAMES["achievement_videos"])

            result.append(
                AchievementPayload(
                    id=achievement.id,
                    title=achievement.title,
                    description=achievement.description,
                    event_date=achievement.event_date.isoformat() if achievement.event_date else None,
                    place=achievement.place,
                    is_collective=achievement.is_collective,
                    file_url=file_url,
                    video_url=video_url,
                    student_id=student.id if student else None,
                    student_name=f"{student.first_name} {student.last_name or ''}".strip() if student else None,
                    student_avatar_url=file_service.get_file_url(image_key, BUCKET_NAMES["student_photos"]) if image_key else None,
                ).to_dict()
            )

        return result

    def delete_achievement(self, db: Session, *, ctx: AccessContext, achievement_id: int):
        try:
            AchievementPolicy.require_manage_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to delete achievement") from exc

        achievement = achievement_repository.get_by_id(db, achievement_id=achievement_id)
        if not achievement:
            raise NotFoundError("Achievement not found")

        with UnitOfWork(db):
            if achievement.certificate_url:
                file_service.delete_file(achievement.certificate_url, BUCKET_NAMES["certificates"])
            if achievement.video_url:
                file_service.delete_file(achievement.video_url, BUCKET_NAMES["achievement_videos"])
            db.delete(achievement)
            db.flush()

    def get_student_achievements_payload(self, db: Session, student_id: int, *, ctx: AccessContext):
        try:
            AchievementPolicy.require_view_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to student achievements") from exc
        if not self._can_view_student(db, ctx=ctx, student_id=student_id):
            raise PermissionDenied("Access denied to this student's achievements")

        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise NotFoundError("Student not found")

        user_achievements = achievement_repository.list_for_student(db, student_id=student_id)
        collective_achievements = db.query(Achievement).filter(Achievement.is_collective == True).all()

        all_achievements = []
        seen_ids = set()

        for ua in user_achievements:
            achievement = ua.achievement
            seen_ids.add(achievement.id)
            file_url = None
            if achievement.certificate_url:
                file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

            all_achievements.append(
                AchievementPayload(
                    id=achievement.id,
                    title=achievement.title,
                    description=achievement.description,
                    event_date=achievement.event_date.isoformat() if achievement.event_date else None,
                    place=achievement.place,
                    is_collective=False,
                    file_url=file_url,
                    video_url=file_service.get_file_url(achievement.video_url, BUCKET_NAMES["achievement_videos"]) if achievement.video_url and achievement.is_public else None,
                    awarded_at=ua.awarded_at.isoformat() if ua.awarded_at else None,
                ).to_dict()
            )

        for achievement in collective_achievements:
            if achievement.id not in seen_ids:
                file_url = None
                if achievement.certificate_url:
                    file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

                all_achievements.append(
                    AchievementPayload(
                        id=achievement.id,
                        title=achievement.title,
                        description=achievement.description,
                        event_date=achievement.event_date.isoformat() if achievement.event_date else None,
                        place=achievement.place,
                        is_collective=True,
                        file_url=file_url,
                        video_url=file_service.get_file_url(achievement.video_url, BUCKET_NAMES["achievement_videos"]) if achievement.video_url and achievement.is_public else None,
                        awarded_at=None,
                    ).to_dict()
                )

        return all_achievements

    async def upload_achievement_media(self, db: Session, *, ctx: AccessContext, achievement_id: int, file, logger=None):
        try:
            AchievementPolicy.require_manage_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to upload achievement media") from exc

        achievement = achievement_repository.get_by_id(db, achievement_id=achievement_id)
        if not achievement:
            raise NotFoundError("Achievement not found")

        with UnitOfWork(db):
            if file.content_type in ["video/mp4", "video/mpeg"]:
                file_id = await file_service.upload_achievement_video(file)
                achievement.video_url = file_id
                response_url = file_service.get_file_url(file_id, BUCKET_NAMES["achievement_videos"])
                result = {
                    "message": "achievement video updated",
                    "achievement_id": achievement.id,
                    "video_url": response_url,
                }
            else:
                file_id = await file_service.upload_achievement_media(file)
                achievement.certificate_url = file_id
                response_url = file_service.get_file_url(file_id, BUCKET_NAMES["certificates"])
                result = {
                    "message": "achievement media updated",
                    "achievement_id": achievement.id,
                    "file_url": response_url,
                }

            return result

    async def upload_achievement_video(self, db: Session, *, ctx: AccessContext, achievement_id: int, file):
        try:
            AchievementPolicy.require_manage_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to upload achievement video") from exc

        achievement = achievement_repository.get_by_id(db, achievement_id=achievement_id)
        if not achievement:
            raise NotFoundError("Achievement not found")

        with UnitOfWork(db):
            file_id = await file_service.upload_achievement_video(file)
            achievement.video_url = file_id
            return {
                "message": "achievement video uploaded",
                "achievement_id": achievement.id,
                "video_url": file_service.get_file_url(file_id, BUCKET_NAMES["achievement_videos"]),
            }

    async def create_achievement_from_form(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, event_date: str | None, place: str | None, assignment_type: str, student_id: int | None, file, logger=None):
        try:
            AchievementPolicy.require_manage_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to create achievement") from exc

        parsed_date = None
        if event_date:
            try:
                parsed_date = datetime.fromisoformat(event_date)
            except ValueError:
                raise ConflictError("Invalid date format")

        if description is None:
            description = ""

        if place:
            description = f"{description}\nРезультат: {place}".strip()

        if assignment_type not in ["collective", "individual"]:
            raise ConflictError("Invalid assignment_type")

        if assignment_type == "individual" and student_id is None:
            raise ConflictError("student_id required for individual assignment")

        if assignment_type == "collective" and student_id is not None:
            raise ConflictError("student_id should not be provided for collective assignment")

        if assignment_type == "individual" and not accounts_facade.is_student(db, user_id=student_id):
            raise NotFoundError("Student not found")

        file_id = None
        file_url = None
        if file:
            if getattr(file, "content_type", "") in ["video/mp4", "video/mpeg"]:
                file_id = await file_service.upload_achievement_video(file)
                file_url = file_service.get_file_url(file_id, BUCKET_NAMES["achievement_videos"])
                achievement = Achievement(
                    title=title.strip(),
                    description=description,
                    event_date=parsed_date,
                    place=place,
                    is_collective=(assignment_type == "collective"),
                    is_public=True,
                    video_url=file_id,
                )
            else:
                file_id = await file_service.upload_achievement_media(file)
                file_url = file_service.get_file_url(file_id, BUCKET_NAMES["certificates"])
                achievement = Achievement(
                    title=title.strip(),
                    description=description,
                    event_date=parsed_date,
                    place=place,
                    is_collective=(assignment_type == "collective"),
                    certificate_url=file_id,
                )
        else:
            achievement = Achievement(
                title=title.strip(),
                description=description,
                event_date=parsed_date,
                place=place,
                is_collective=(assignment_type == "collective"),
            )

        with UnitOfWork(db):
            achievement_repository.create(db, achievement)

            if assignment_type == "individual":
                achievement_repository.create_assignment(db, UserAchievement(user_id=student_id, achievement_id=achievement.id))

            result = {
                "message": "achievement created",
                "achievement_id": achievement.id,
                "student_id": student_id,
            }
            if file_id:
                result["file_id"] = file_id
            if file_url:
                result["file_url"] = file_url
            return result
        if file_id:
            result["file_id"] = file_id
        if file_url:
            result["file_url"] = file_url
        return result

    def assign_achievement(self, db: Session, *, ctx: AccessContext, achievement_id: int, user_id: int):
        try:
            AchievementPolicy.require_manage_achievements(ctx)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to assign achievement") from exc

        achievement = achievement_repository.get_by_id(db, achievement_id=achievement_id)
        if not achievement:
            raise NotFoundError("Achievement not found")

        if achievement.is_collective:
            raise ConflictError("Collective achievement cannot be assigned to an individual")

        if not accounts_facade.is_student(db, user_id=user_id):
            raise NotFoundError("Student not found")

        existing = achievement_repository.get_assignment(db, user_id=user_id, achievement_id=achievement_id)
        if existing:
            raise ConflictError("Already assigned")

        with UnitOfWork(db):
            assignment = achievement_repository.create_assignment(db, UserAchievement(user_id=user_id, achievement_id=achievement_id))
            return assignment


achievement_service = AchievementService()
