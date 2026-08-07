from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import PermissionDenied
from db.minio_client import BUCKET_NAMES
from profile.dtos.dashboard_dto import DashboardPayload, StudentTaskPayload
from profile.policies.dashboard_policy import DashboardPolicy
from profile.repositories.dashboard_repository import dashboard_repository
from services.file_service import file_service
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia
from models.domains.auth import User


class DashboardService:
    def get_dashboard_payload(self, db: Session, *, ctx: AccessContext):
        try:
            DashboardPolicy.require_view_own_dashboard(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to dashboard") from exc

        user_id = ctx.user_id
        profile = dashboard_repository.get_profile(db, user_id=user_id)
        user = dashboard_repository.get_user(db, user_id=user_id)
        tasks = dashboard_repository.get_tasks(db, user_id=user_id)
        videos = dashboard_repository.get_videos(db, user_id=user_id)

        user_achievements = dashboard_repository.get_user_achievements(db, user_id=user_id)

        individual_achievements = []
        collective_awarded_at = {}

        for ua in user_achievements:
            achievement = ua.achievement
            if not achievement:
                continue
            if achievement.is_collective:
                collective_awarded_at[achievement.id] = ua.awarded_at.isoformat() if ua.awarded_at else None
                continue

            individual_achievements.append({
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
                "place": achievement.place,
                "is_collective": False,
                "file_url": file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"]) if achievement.certificate_url else None,
                "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["videos"]) if achievement.video_url else None,
                "awarded_at": ua.awarded_at.isoformat() if ua.awarded_at else None,
            })

        collective_achievements = dashboard_repository.get_collective_achievements(db)
        collective_achievements_result = []

        for achievement in collective_achievements:
            collective_achievements_result.append({
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
                "place": achievement.place,
                "is_collective": True,
                "file_url": file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"]) if achievement.certificate_url else None,
                "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["videos"]) if achievement.video_url else None,
                "awarded_at": collective_awarded_at.get(achievement.id),
            })

        achievement_videos = [
            {
                "id": achievement["id"],
                "title": achievement["title"],
                "description": achievement["description"],
                "event_date": achievement["event_date"],
                "place": achievement["place"],
                "file_url": achievement["file_url"],
                "video_url": achievement["video_url"],
                "awarded_at": achievement["awarded_at"],
            }
            for achievement in individual_achievements
            if achievement.get("video_url")
        ] + [
            {
                "id": achievement["id"],
                "title": achievement["title"],
                "description": achievement["description"],
                "event_date": achievement["event_date"],
                "place": achievement["place"],
                "is_collective": achievement["is_collective"],
                "file_url": achievement["file_url"],
                "video_url": achievement["video_url"],
                "awarded_at": achievement["awarded_at"],
            }
            for achievement in collective_achievements_result
            if achievement.get("video_url")
        ]

        user_rating = profile.rating_points if profile else 0
        higher_rank_count = db.query(StudentProfile.rating_points).filter(StudentProfile.rating_points > user_rating).distinct().count()
        total_students = db.query(StudentProfile).count()
        user_place = higher_rank_count + 1 if profile else None

        history_records = dashboard_repository.get_history(db, user_id=user_id)

        history = []
        current_points = user_rating
        for record in history_records:
            history.append({
                "timestamp": record.created_at.isoformat() if record.created_at else None,
                "points_change": record.points_change,
                "reason": record.reason,
                "points_after": current_points,
                "direction": "up" if record.points_change > 0 else "down" if record.points_change < 0 else "same",
                "place_estimate": db.query(StudentProfile.rating_points).filter(StudentProfile.rating_points > current_points).distinct().count() + 1,
            })
            current_points -= record.points_change
        history.reverse()

        leaderboard_profiles = dashboard_repository.get_leaderboard_profiles(db)
        leaderboard = []
        previous_rating = None
        current_place = 0

        for profile_item in leaderboard_profiles:
            if profile_item.rating_points != previous_rating:
                current_place += 1
                previous_rating = profile_item.rating_points

            last_history = (
                db.query(RatingsHistory)
                .filter(RatingsHistory.student_id == profile_item.user_id)
                .order_by(RatingsHistory.created_at.desc())
                .first()
            )

            movement = "same"
            if last_history:
                if last_history.points_change > 0:
                    movement = "up"
                elif last_history.points_change < 0:
                    movement = "down"

            leaderboard.append({
                "place": current_place,
                "user_id": profile_item.user.id,
                "full_name": f"{profile_item.user.first_name} {profile_item.user.last_name}".strip(),
                "rating": profile_item.rating_points,
                "movement": movement,
            })

        return DashboardPayload(
            user_id=user_id,
            rating=profile.rating_points if profile else 0,
            tasks=len(tasks),
            place=user_place,
            total_students=total_students,
            history=history,
            leaderboard=leaderboard,
            videos=[{"id": v.id, "url": file_service.get_file_url(v.video_url, BUCKET_NAMES["videos"])} for v in videos],
            achievement_videos=achievement_videos,
            achievements={"individual": individual_achievements, "collective": collective_achievements_result},
            user={
                "full_name": f"{user.first_name} {user.last_name}".strip() if user else None,
                "email": user.email if user else None,
                "image_url": file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"]) if profile and profile.image_url else None,
            },
        ).to_dict()

    def get_student_tasks_payload(self, db: Session, *, ctx: AccessContext):
        try:
            DashboardPolicy.require_view_own_tasks(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to student tasks") from exc

        student_tasks = dashboard_repository.get_student_tasks(db, user_id=ctx.user_id)

        return [
            StudentTaskPayload(
                student_task_id=st.id,
                task_id=st.task.id if st.task else None,
                title=st.task.title if st.task else None,
                description=st.task.description if st.task else None,
                category_name=st.task.category.name if st.task and st.task.category else None,
                status=st.status,
                score=st.score,
                max_score=st.task.max_score if st.task else None,
                has_video=len(st.media) > 0,
                videos=[{"media_id": media.id, "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"])} for media in st.media],
            ).to_dict()
            for st in student_tasks
        ]


dashboard_service = DashboardService()
