from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import DomainError, to_http_exception
from core.permissions import get_access_context
from db.database import get_db
from public.facade import public_facade
from public.schemas import PublicAchievementVideosResponse

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/leaderboard")
def get_public_leaderboard(db: Session = Depends(get_db)):
    return public_facade.get_public_leaderboard(db)

@router.get("/achievements/videos", response_model=PublicAchievementVideosResponse)
def get_public_achievement_videos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return public_facade.get_public_achievement_videos(db, limit=limit, offset=offset)


@router.get("/student/{student_id}/videos")
def get_student_videos(
    student_id: int,
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    try:
        return public_facade.get_student_videos(db, student_id, ctx=ctx)
    except DomainError as exc:
        to_http_exception(exc)
