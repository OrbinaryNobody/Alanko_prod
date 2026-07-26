from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from core.permissions import get_current_user, has_permission, Permission
from db.database import get_db


def get_current_teacher_or_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not any(
        has_permission(current_user, perm, db)
        for perm in (
            Permission.MANAGE_STUDENTS,
            Permission.MANAGE_TASKS,
            Permission.MANAGE_ACHIEVEMENTS,
        )
    ):
        raise HTTPException(status_code=403, detail="Teacher or admin required")

    return current_user["user_id"]
