from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import Permission, require_permission
from db.database import get_db
from profile.facade import profile_facade

router = APIRouter(prefix="/dashboard", tags=["profile-dashboard"])


@router.get("")
def dashboard(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_OWN_DASHBOARD)),
    db: Session = Depends(get_db),
):
    return profile_facade.get_dashboard_payload(db, ctx=ctx)
