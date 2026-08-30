from sqlalchemy.orm import Session, joinedload

from core.exceptions import NotFoundError, PermissionDenied
from db.minio_client import BUCKET_NAMES
from models.domains.achievements import Achievement
from models.domains.auth import User
from models.domains.education import Group, GroupEnrollment, GroupMember
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia
from public.dtos.public_dto import (
    PublicLeaderboardItem,
    PublicLeaderboardPlace,
    PublicLeaderboardPayload,
    PublicAchievementVideoItem,
    PublicStudentVideoItem,
    PublicStudentVideosPayload,
)
from infrastructure.storage.file_service import file_service


class PublicService:
    def get_public_leaderboard(self, db: Session):
        eligible_enrollments = (
            db.query(GroupEnrollment)
            .join(Group)
            .filter(
                GroupEnrollment.status == "active",
                Group.status == "active",
                Group.leaderboard_enabled.is_(True),
            )
            .all()
        )

        overall_scores_by_user = {}
        for enrollment in eligible_enrollments:
            overall_scores_by_user[enrollment.student_id] = overall_scores_by_user.get(enrollment.student_id, 0) + sum(
                task.grade or 0 for task in enrollment.tasks
            )

        ranking_scores = sorted(
            [
                {"user_id": student_id, "rating": rating}
                for student_id, rating in overall_scores_by_user.items()
            ],
            key=lambda item: (-item["rating"], item["user_id"]),
        )

        top_3_students = []
        for item in ranking_scores[:3]:
            user = db.query(User).filter(User.id == item["user_id"]).first()
            if not user:
                continue

            profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
            image_url = file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"]) if profile and profile.image_url else None

            top_3_students.append(
                PublicLeaderboardItem(
                    user_id=user.id,
                    full_name=f"{user.first_name} {user.last_name}".strip(),
                    rating=item["rating"],
                    image_url=image_url,
                    role=getattr(profile, "role", "Студент") if profile else "Студент",
                    description=getattr(profile, "bio", "") if profile else "",
                )
            )

        profile_ids = [item["user_id"] for item in ranking_scores[:5]]
        history_rows = (
            db.query(RatingsHistory)
            .filter(RatingsHistory.student_id.in_(profile_ids))
            .order_by(RatingsHistory.student_id, RatingsHistory.created_at.desc(), RatingsHistory.id.desc())
            .all()
        )
        latest_history = {}
        for history in history_rows:
            latest_history.setdefault(history.student_id, history)

        top_5_leaderboard = []
        for place, item in enumerate(ranking_scores[:5], start=1):
            user = db.query(User).filter(User.id == item["user_id"]).first()
            if not user:
                continue

            last_history = latest_history.get(user.id)
            movement = "same"
            if last_history:
                if last_history.points_change > 0:
                    movement = "up"
                elif last_history.points_change < 0:
                    movement = "down"

            top_5_leaderboard.append(
                PublicLeaderboardPlace(
                    place=place,
                    user_id=user.id,
                    full_name=f"{user.first_name} {user.last_name}".strip(),
                    rating=item["rating"],
                    movement=movement,
                )
            )

        return PublicLeaderboardPayload(
            top_3_students=top_3_students,
            top_5_leaderboard=top_5_leaderboard,
            timestamp=None,
        ).to_dict()

    def get_student_videos(self, db: Session, student_id: int, *, ctx):
        if not ctx.is_admin and ctx.user_id != student_id:
            has_group_access = (
                db.query(GroupEnrollment)
                .join(GroupMember, GroupMember.group_id == GroupEnrollment.group_id)
                .filter(
                    GroupEnrollment.student_id == student_id,
                    GroupEnrollment.status == "active",
                    GroupMember.user_id == ctx.user_id,
                )
                .first()
            )
            if not has_group_access and not ctx.has_role("secretary"):
                raise PermissionDenied("Access denied to student videos")

        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise NotFoundError("Студент не найден")

        videos = (
            db.query(TaskMedia)
            .join(StudentTask, TaskMedia.student_task_id == StudentTask.id)
            .join(Task, StudentTask.task_id == Task.id)
            .options(joinedload(TaskMedia.student_task).joinedload(StudentTask.task).joinedload(Task.category))
            .filter(StudentTask.student_id == student_id, TaskMedia.is_public == True)
            .order_by(TaskMedia.created_at.desc())
            .all()
        )

        result_videos = []
        for media in videos:
            source = media.video_url or ""
            if source.startswith("http://") or source.startswith("https://"):
                video_url = source
            else:
                video_url = file_service.get_file_url(source, BUCKET_NAMES["videos"])

            task_title = "Выполненное задание"
            category_name = ""
            if media.student_task and media.student_task.task:
                task_title = media.student_task.task.title or task_title
                category_name = media.student_task.task.category.name if media.student_task.task.category else ""

            result_videos.append(
                PublicStudentVideoItem(
                    id=media.id,
                    task_name=task_title,
                    category=category_name,
                    video_url=video_url,
                    uploaded_at=media.created_at.isoformat() if media.created_at else None,
                )
            )

        return PublicStudentVideosPayload(
            student_id=student.id,
            full_name=f"{student.first_name} {student.last_name}".strip(),
            videos=result_videos,
        ).to_dict()

    def get_public_achievement_videos(self, db: Session, *, limit: int = 20, offset: int = 0):
        achievements = (
            db.query(Achievement)
            .filter(Achievement.video_url.is_not(None), Achievement.is_public.is_(True))
            .order_by(Achievement.event_date.desc().nullslast(), Achievement.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "items": [
                PublicAchievementVideoItem(
                    id=achievement.id,
                    title=achievement.title,
                    description=achievement.description,
                    video_url=file_service.get_file_url(
                        achievement.video_url,
                        BUCKET_NAMES["achievement_videos"],
                    ),
                    event_date=achievement.event_date.isoformat() if achievement.event_date else None,
                ).to_dict()
                for achievement in achievements
            ]
        }


public_service = PublicService()
