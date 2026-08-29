from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from achievements.dtos.achievement_dto import AchievementCreateResponse, AchievementAssignmentResponse, AchievementUploadResponse
from achievements.facade import achievements_facade
from core.access import AccessContext
from core.exceptions import DomainError, to_http_exception
from core.permissions import require_manage_achievements, require_upload_media, require_view_achievements
from db.database import get_db
from achievements.schemas.achievment import AssignAchievement

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("")
def get_achievements(
    ctx: AccessContext = Depends(require_view_achievements),
    db: Session = Depends(get_db),
):
    return {"data": achievements_facade.get_achievements_payload(db, ctx=ctx)}


@router.delete("/{achievement_id}", status_code=204)
def delete_achievement(
    achievement_id: int,
    ctx: AccessContext = Depends(require_manage_achievements),
    db: Session = Depends(get_db),
):
    achievements_facade.delete_achievement(db, ctx=ctx, achievement_id=achievement_id)


@router.get("/student/{student_id}")
def get_student_achievements(
    student_id: int,
    ctx: AccessContext = Depends(require_view_achievements),
    db: Session = Depends(get_db),
):
    return {"data": achievements_facade.get_student_achievements_payload(db, student_id, ctx=ctx)}


@router.post("/{achievement_id}/upload-media")
async def upload_achievement_media(
    achievement_id: int,
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(require_upload_media),
    db: Session = Depends(get_db),
):
    payload = await achievements_facade.upload_achievement_media(db, ctx=ctx, achievement_id=achievement_id, file=file, logger=None)
    return AchievementUploadResponse(
        message=payload["message"],
        achievement_id=payload["achievement_id"],
        file_url=payload.get("file_url"),
        video_url=payload.get("video_url"),
    ).to_dict()


@router.post("/{achievement_id}/upload-video")
async def upload_achievement_video(
    achievement_id: int,
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(require_upload_media),
    db: Session = Depends(get_db),
):
    payload = await achievements_facade.upload_achievement_video(db, ctx=ctx, achievement_id=achievement_id, file=file)
    return AchievementUploadResponse(
        message=payload["message"],
        achievement_id=payload["achievement_id"],
        file_url=payload.get("file_url"),
        video_url=payload.get("video_url"),
    ).to_dict()


@router.post("/create")
async def create_achievement(
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(None),
    place: str = Form(None),
    assignment_type: str = Form(...),
    student_id: int = Form(None),
    file: UploadFile = File(None),
    ctx: AccessContext = Depends(require_manage_achievements),
    db: Session = Depends(get_db),
):
    payload = await achievements_facade.create_achievement_from_form(
        db,
        ctx=ctx,
        title=title,
        description=description,
        event_date=event_date,
        place=place,
        assignment_type=assignment_type,
        student_id=student_id,
        file=file,
        logger=None,
    )
    return AchievementCreateResponse.from_payload(payload).to_dict()


@router.post("/assign")
def assign_achievement(
    data: AssignAchievement,
    ctx: AccessContext = Depends(require_manage_achievements),
    db: Session = Depends(get_db),
):
    try:
        assignment = achievements_facade.assign_achievement(
            db,
            ctx=ctx,
            achievement_id=data.achievement_id,
            user_id=data.user_id,
        )
    except DomainError as exc:
        to_http_exception(exc)

    return AchievementAssignmentResponse(achievement_id=data.achievement_id, user_id=data.user_id, assigned_by=ctx.user_id).to_dict()
