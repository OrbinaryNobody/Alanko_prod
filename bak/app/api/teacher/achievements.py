from datetime import datetime
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from db.minio_client import BUCKET_NAMES
from models import Achievement, User, UserAchievement
from schemas.achievment import AchievementCreate, AssignAchievement
from services.data_access import achievement_service
from services.file_service import file_service

from core.permissions import require_upload_media
from .common import get_current_teacher_or_admin

router = APIRouter(prefix="/teacher", tags=["teacher"])
logger = logging.getLogger("alanko.teacher")


@router.get("/achievements")
def get_achievements(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    return {"data": achievement_service.get_achievements_payload(db)}


@router.get("/student-achievements/{student_id}")
def get_student_achievements(
    student_id: int,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    return {"data": achievement_service.get_student_achievements_payload(db, student_id)}


@router.post("/achievements/{achievement_id}/upload-media")
async def upload_achievement_media(
    achievement_id: int,
    file: UploadFile = File(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    current_user: dict = Depends(require_upload_media),
    db: Session = Depends(get_db)
):
    return await achievement_service.upload_achievement_media(db, achievement_id=achievement_id, file=file, logger=logger)


@router.post("/achievements/{achievement_id}/upload-video")
async def upload_achievement_video(
    achievement_id: int,
    file: UploadFile = File(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    current_user: dict = Depends(require_upload_media),
    db: Session = Depends(get_db)
):
    return await achievement_service.upload_achievement_video(db, achievement_id=achievement_id, file=file)


@router.post("/achievements/create")
async def create_achievement(
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(None),
    place: str = Form(None),
    assignment_type: str = Form(...),
    student_id: int = Form(None),
    file: UploadFile = File(None),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    return await achievement_service.create_achievement_from_form(
        db,
        title=title,
        description=description,
        event_date=event_date,
        place=place,
        assignment_type=assignment_type,
        student_id=student_id,
        file=file,
        logger=logger,
    )


@router.post("/achievements/assign")
def assign_achievement(
    data: AssignAchievement,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    try:
        achievement_service.assign_achievement(
            db,
            achievement_id=data.achievement_id,
            user_id=data.user_id,
        )
    except HTTPException:
        raise

    return {
        "message": "assigned",
        "assigned_by": user_id
    }
