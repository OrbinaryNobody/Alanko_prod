"""
Публичные endpoints для фронтенда (без требования аутентификации).
Используются на главной странице (index.html) для отображения:
- ТОП-3 лучших студентов
- ТОП-5 лидерборда с динамикой
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from db.database import get_db
from models import User, StudentProfile, RatingsHistory, StudentTask, TaskMedia, Task
from services.file_service import file_service
from db.minio_client import BUCKET_NAMES

router = APIRouter(prefix="/public", tags=["public"])


# =========================
# Получить ТОП-3 студентов и ТОП-5 лидерборда (БЕЗ АУТЕНТИФИКАЦИИ)
# =========================
@router.get("/leaderboard")
def get_public_leaderboard(db: Session = Depends(get_db)):
    """
    Возвращает публичные данные для главной страницы:
    - top_3_students: ТОП-3 студентов по баллам (для блока "Лучшие ученики")
    - top_5_leaderboard: ТОП-5 студентов (для таблицы "Лидеров")
    
    Данные получены из StudentProfile.rating_points (баллы).
    Изображения преобразованы в полные URL из MinIO.
    """
    
    # Получаем всех студентов с их профилями, отсортированные по баллам (DESC)
    all_profiles = (
        db.query(StudentProfile)
        .join(User)
        .options(joinedload(StudentProfile.user))
        .order_by(StudentProfile.rating_points.desc())
        .all()
    )
    
    # ===== ТОП-3 СТУДЕНТОВ =====
    top_3_students = []
    for profile in all_profiles[:3]:
        user = profile.user
        image_url = file_service.get_file_url(
            profile.image_url,
            BUCKET_NAMES["student_photos"]
        ) if profile.image_url else None
        
        top_3_students.append({
            "user_id": user.id,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "rating": profile.rating_points,
            "image_url": image_url,
            "role": profile.role if hasattr(profile, 'role') else "Студент",
            "description": profile.bio if hasattr(profile, 'bio') else ""
        })
    
    # ===== ТОП-5 ЛИДЕРБОРДА =====
    top_5_leaderboard = []
    place = 1
    for profile in all_profiles[:5]:
        user = profile.user
        
        # Определяем движение (up/down/same) из последней записи истории рейтинга
        last_history = db.query(RatingsHistory).filter(
            RatingsHistory.student_id == user.id
        ).order_by(RatingsHistory.created_at.desc()).first()
        
        movement = "same"
        if last_history:
            if last_history.points_change > 0:
                movement = "up"
            elif last_history.points_change < 0:
                movement = "down"
        
        top_5_leaderboard.append({
            "place": place,
            "user_id": user.id,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "rating": profile.rating_points,
            "movement": movement
        })
        
        place += 1
    
    return {
        "top_3_students": top_3_students,
        "top_5_leaderboard": top_5_leaderboard,
        "timestamp": None  # Можно добавить время обновления если нужно
    }


# =========================
# Получить видео студента (публично)
# =========================
@router.get("/student/{student_id}/videos")
def get_student_videos(student_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список публичных видео, загруженных к заданиям студента.
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    videos = (
        db.query(TaskMedia)
        .join(StudentTask, TaskMedia.student_task_id == StudentTask.id)
        .join(Task, StudentTask.task_id == Task.id)
        .options(
            joinedload(TaskMedia.student_task).joinedload(StudentTask.task).joinedload(Task.category)
        )
        .filter(
            StudentTask.student_id == student_id,
            TaskMedia.is_public == True
        )
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

        result_videos.append({
            "id": media.id,
            "task_name": task_title,
            "category": category_name,
            "video_url": video_url,
            "uploaded_at": media.created_at.isoformat() if media.created_at else None
        })

    return {
        "student_id": student.id,
        "full_name": f"{student.first_name} {student.last_name}".strip(),
        "videos": result_videos
    }
