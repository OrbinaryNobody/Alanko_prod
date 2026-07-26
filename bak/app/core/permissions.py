from typing import Callable, Optional, Set

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload

from core.security import verify_token
from db.database import get_db
from models.all_models import User, UserRole

security = HTTPBearer()


class Permission:
    MANAGE_STUDENTS = "manage_students"
    MANAGE_TASKS = "manage_tasks"
    MANAGE_USERS = "manage_users"
    MANAGE_ACHIEVEMENTS = "manage_achievements"
    UPLOAD_MEDIA = "upload_media"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_OWN_ACHIEVEMENTS = "view_own_achievements"
    VIEW_STUDENT_TASKS = "view_student_tasks"
    VIEW_ASSESSMENT = "view_assessment"


ROLE_PERMISSIONS = {
    "student": {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_OWN_ACHIEVEMENTS,
        Permission.VIEW_STUDENT_TASKS,
    },
    "teacher": {
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_TASKS,
        Permission.MANAGE_ACHIEVEMENTS,
        Permission.UPLOAD_MEDIA,
        Permission.VIEW_ASSESSMENT,
    },
    "admin": {
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_TASKS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ACHIEVEMENTS,
        Permission.UPLOAD_MEDIA,
        Permission.VIEW_ASSESSMENT,
    },
}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def get_user_roles(user: dict, db: Optional[Session] = None) -> Set[str]:
    roles = set()
    role_name = user.get("role")
    if role_name:
        roles.add(role_name)

    if db is not None and user.get("user_id") is not None:
        user_obj = (
            db.query(User)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .filter(User.id == user["user_id"])
            .first()
        )
        if user_obj:
            roles = {ur.role.name for ur in user_obj.roles if ur.role}

    return roles


def has_permission(user: dict, permission: str, db: Optional[Session] = None) -> bool:
    if not user:
        return False

    roles = get_user_roles(user, db)
    for role in roles:
        if permission in ROLE_PERMISSIONS.get(role, set()):
            return True
    return False


def can_manage_students(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.MANAGE_STUDENTS, db)


def can_manage_tasks(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.MANAGE_TASKS, db)


def can_manage_users(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.MANAGE_USERS, db)


def can_manage_achievements(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.MANAGE_ACHIEVEMENTS, db)


def can_upload_media(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.UPLOAD_MEDIA, db)


def can_view_dashboard(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.VIEW_DASHBOARD, db)


def can_view_own_achievements(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.VIEW_OWN_ACHIEVEMENTS, db)


def can_view_student_tasks(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.VIEW_STUDENT_TASKS, db)


def can_view_assessment(user: dict, db: Optional[Session] = None) -> bool:
    return has_permission(user, Permission.VIEW_ASSESSMENT, db)


def require_permission(permission: str) -> Callable:
    def dependency(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not has_permission(current_user, permission, db):
            raise HTTPException(status_code=403, detail=f"Access denied: {permission} permission required")
        return current_user

    return dependency


require_manage_students = require_permission(Permission.MANAGE_STUDENTS)
require_manage_tasks = require_permission(Permission.MANAGE_TASKS)
require_manage_users = require_permission(Permission.MANAGE_USERS)
require_manage_achievements = require_permission(Permission.MANAGE_ACHIEVEMENTS)
require_upload_media = require_permission(Permission.UPLOAD_MEDIA)
require_view_dashboard = require_permission(Permission.VIEW_DASHBOARD)
require_view_own_achievements = require_permission(Permission.VIEW_OWN_ACHIEVEMENTS)
require_view_assessment = require_permission(Permission.VIEW_ASSESSMENT)
require_student = require_permission(Permission.VIEW_STUDENT_TASKS)
