from sqlalchemy.orm import Session, joinedload

from core.exceptions import NotFoundError
from db.minio_client import BUCKET_NAMES
from models.domains.auth import User
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia
from public.dtos.public_dto import (
    PublicLeaderboardItem,
    PublicLeaderboardPlace,
    PublicLeaderboardPayload,
    PublicStudentVideoItem,
    PublicStudentVideosPayload,
)
from services.file_service import file_service


class PublicService:
    def get_public_leaderboard(self, db: Session):
        all_profiles = (
            db.query(StudentProfile)
            .join(User)
            .options(joinedload(StudentProfile.user))
            .order_by(StudentProfile.rating_points.desc())
            .all()
        )

        top_3_students = []
        for profile in all_profiles[:3]:
            user = profile.user
            image_url = file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"]) if profile.image_url else None

            top_3_students.append(
                PublicLeaderboardItem(
                    user_id=user.id,
                    full_name=f"{user.first_name} {user.last_name}".strip(),
                    rating=profile.rating_points,
                    image_url=image_url,
                    role=getattr(profile, "role", "Студент"),
                    description=getattr(profile, "bio", ""),
                )
            )

        top_5_leaderboard = []
        place = 1
        for profile in all_profiles[:5]:
            user = profile.user
            last_history = db.query(RatingsHistory).filter(RatingsHistory.student_id == user.id).order_by(RatingsHistory.created_at.desc()).first()

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
                    rating=profile.rating_points,
                    movement=movement,
                )
            )
            place += 1

        return PublicLeaderboardPayload(
            top_3_students=top_3_students,
            top_5_leaderboard=top_5_leaderboard,
            timestamp=None,
        ).to_dict()

    def get_student_videos(self, db: Session, student_id: int):
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


public_service = PublicService()
