from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.exceptions import DomainError, to_http_exception
from db.database import get_db
from public.facade import public_facade

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/leaderboard")
def get_public_leaderboard(db: Session = Depends(get_db)):
    return public_facade.get_public_leaderboard(db)


@router.get("/student/{student_id}/videos")
def get_student_videos(student_id: int, db: Session = Depends(get_db)):
    try:
        return public_facade.get_student_videos(db, student_id)
    except DomainError as exc:
        to_http_exception(exc)
