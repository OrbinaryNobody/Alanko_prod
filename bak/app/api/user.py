from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.orm import Session, joinedload
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.all_models import Achievement, UserAchievement, RatingsHistory
from services.file_service import file_service
from db.minio_client import BUCKET_NAMES


from core.access import AccessContext
from core.permissions import Permission, get_current_user, get_access_context, has_permission, require_permission
from db.database import get_db
from models import User, StudentTask, StudentProfile, TaskMedia, Task

router = APIRouter(prefix="/user", tags=["user"])
security = HTTPBearer()

logger = logging.getLogger("alanko.user")


# =========================
# ONLY STUDENT ACCESS
# =========================
def require_student(ctx: AccessContext = Depends(get_access_context), db: Session = Depends(get_db)):
    if not has_permission(ctx, Permission.VIEW_OWN_TASKS, db) and not has_permission(ctx, Permission.VIEW_OWN_DASHBOARD, db):
        raise HTTPException(
            status_code=403,
            detail="Only students can access this resource"
        )
    return ctx


# =========================
# Достижение 
# =========================
@router.get("/dashboard")
def dashboard(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_DASHBOARD)),
    db: Session = Depends(get_db)
):
    user_id = ctx.user_id
    logger.info(f"/user/dashboard requested for user_id={user_id}")

    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == user_id
    ).first()

    user = db.query(User).filter(User.id == user_id).first()

    tasks = db.query(StudentTask).filter(
        StudentTask.student_id == user_id
    ).all()

    videos = db.query(TaskMedia).join(StudentTask).filter(
        StudentTask.student_id == user_id
    ).all()

    user_achievements = (
        db.query(UserAchievement)
        .options(joinedload(UserAchievement.achievement))
        .filter(UserAchievement.user_id == user_id)
        .all()
    )

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
            "awarded_at": ua.awarded_at.isoformat() if ua.awarded_at else None
        })

    collective_achievements = db.query(Achievement).filter(
        Achievement.is_collective == True
    ).all()

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
            "awarded_at": collective_awarded_at.get(achievement.id)
        })

    achievement_videos = [
        {
            "id": achievement["id"],
            "title": achievement["title"],
            "description": achievement["description"],
            "event_date": achievement["event_date"],
            "place": achievement["place"],
            # "is_collective": achievement["is_collective"],
            "file_url": achievement["file_url"],
            "video_url": achievement["video_url"],
            "awarded_at": achievement["awarded_at"]
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
            "awarded_at": achievement["awarded_at"]
        }
        for achievement in collective_achievements_result
        if achievement.get("video_url")
    ]
    logger.info("Found %d achievement_videos and %d task videos for user %s", len(achievement_videos), len(videos), user_id)
    try:
        logger.debug("achievement_videos data: %s", achievement_videos)
    except Exception:
        pass

    user_rating = profile.rating_points if profile else 0
    higher_rank_count = db.query(StudentProfile.rating_points).filter(
        StudentProfile.rating_points > user_rating
    ).distinct().count()
    total_students = db.query(StudentProfile).count()
    user_place = higher_rank_count + 1 if profile else None

    history_records = (
        db.query(RatingsHistory)
        .filter(RatingsHistory.student_id == user_id)
        .order_by(RatingsHistory.created_at.desc())
        .all()
    )

    history = []
    current_points = user_rating
    for record in history_records:
        history.append({
            "timestamp": record.created_at.isoformat() if record.created_at else None,
            "points_change": record.points_change,
            "reason": record.reason,
            "points_after": current_points,
            "direction": "up" if record.points_change > 0 else "down" if record.points_change < 0 else "same",
            "place_estimate": db.query(StudentProfile.rating_points).filter(StudentProfile.rating_points > current_points).distinct().count() + 1
        })
        current_points -= record.points_change
    history.reverse()

    leaderboard_profiles = (
        db.query(StudentProfile)
        .join(User)
        .order_by(StudentProfile.rating_points.desc())
        .all()
    )

    leaderboard = []
    previous_rating = None
    current_place = 0

    for profile in leaderboard_profiles:
        if profile.rating_points != previous_rating:
            current_place += 1
            previous_rating = profile.rating_points

        last_history = db.query(RatingsHistory).filter(
            RatingsHistory.student_id == profile.user_id
        ).order_by(RatingsHistory.created_at.desc()).first()

        movement = "same"
        if last_history:
            if last_history.points_change > 0:
                movement = "up"
            elif last_history.points_change < 0:
                movement = "down"

        leaderboard.append({
            "place": current_place,
            "user_id": profile.user.id,
            "full_name": "{} {}".format(profile.user.first_name, profile.user.last_name).strip(),
            "rating": profile.rating_points,
            "movement": movement
        })

    return {
        "user_id": user_id,
        "rating": profile.rating_points if profile else 0,
        "tasks": len(tasks),
        "place": user_place,
        "total_students": total_students,
        "history": history,
        "leaderboard": leaderboard,
        "videos": [
            {
                "id": v.id,
                "url": file_service.get_file_url(v.video_url, BUCKET_NAMES["videos"])
            }
            for v in videos
        ],
        "achievement_videos": achievement_videos,
        "achievements": {
            "individual": individual_achievements,
            "collective": collective_achievements_result
        },
        "user": {
            "full_name": "{} {}".format(user.first_name, user.last_name).strip() if user else None,
            "email": user.email if user else None,
            "image_url": file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"]) if profile and profile.image_url else None
        }
    }


# =========================
# Получить задачи студента
@router.get("/tasks")
def get_student_tasks(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_TASKS)),
    db: Session = Depends(get_db)
):
    user_id = ctx.user_id

    student_tasks = (
        db.query(StudentTask)
        .options(
            joinedload(StudentTask.task).joinedload(Task.category),
            joinedload(StudentTask.media)
        )
        .filter(StudentTask.student_id == user_id)
        .all()
    )

    return [
        {
            "student_task_id": st.id,
            "task_id": st.task.id if st.task else None,
            "title": st.task.title if st.task else None,
            "description": st.task.description if st.task else None,
            "category_name": st.task.category.name if st.task and st.task.category else None,
            "status": st.status,
            "score": st.score,
            "max_score": st.task.max_score if st.task else None,
            "has_video": len(st.media) > 0,
            "videos": [
                {
                    "media_id": media.id,
                    "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"])
                }
                for media in st.media
            ]
        }
        for st in student_tasks
    ]


# =========================
# Получение файла достижения
# =========================
@router.get("/achievements/{achievement_id}")
def get_achievement(
    achievement_id: int,
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_ACHIEVEMENTS)),
    db: Session = Depends(get_db)
):

    user_id = ctx.user_id

    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id
    ).first()

    if not achievement:
        raise HTTPException(status_code=404)

    # =========================
    # Студент — только свои достижения
    # =========================
    if has_permission(ctx, Permission.VIEW_OWN_ACHIEVEMENTS, db):
        record = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()

        if not record:
            raise HTTPException(status_code=403, detail="Not your achievement")

    return {
        "title": achievement.title,
        "description": achievement.description,
        "file": file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])
    }