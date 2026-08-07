from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import Permission, require_permission
from db.database import get_db
from profile.facade import profile_facade

router = APIRouter(prefix="/profile", tags=["profile"])
logger = logging.getLogger("alanko.profile")


@router.get("/dashboard")
def dashboard(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_DASHBOARD)),
    db: Session = Depends(get_db),
):
    logger.info("/profile/dashboard requested for user_id=%s", ctx.user_id)
    return profile_facade.get_dashboard_payload(db, ctx=ctx)


@router.get("/tasks")
def get_student_tasks(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_TASKS)),
    db: Session = Depends(get_db),
):
    return profile_facade.get_student_tasks_payload(db, ctx=ctx)
