from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import get_access_context, has_permission, Permission
from db.database import get_db


def get_current_teacher_or_admin(
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db)
):
    if not any(
        has_permission(ctx, perm, db)
        for perm in (
            Permission.MANAGE_STUDENTS,
            Permission.MANAGE_TASKS,
            Permission.MANAGE_ACHIEVEMENTS,
        )
    ):
        raise HTTPException(status_code=403, detail="Teacher or admin required")

    return ctx.user_id
