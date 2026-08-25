from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import Permission, require_permission
from db.database import get_db
from profile.facade import profile_facade

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/tasks")
def get_student_tasks(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_TASKS)),
    db: Session = Depends(get_db),
):
    return profile_facade.get_student_tasks_payload(db, ctx=ctx)
