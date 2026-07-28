from typing import Callable, Optional, Set, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload

from core.access import AccessContext
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

    VIEW_GROUPS = "view_groups"
    MANAGE_GROUPS = "manage_groups"
    VIEW_PROGRAMS = "view_programs"
    CREATE_PROGRAMS = "create_programs"
    EDIT_PROGRAMS = "edit_programs"
    PUBLISH_PROGRAMS = "publish_programs"
    CREATE_BLOCKS = "create_blocks"
    EDIT_BLOCKS = "edit_blocks"
    PUBLISH_BLOCKS = "publish_blocks"
    CREATE_TASKS = "create_tasks"
    GRADE_TASKS = "grade_tasks"
    CREATE_MANUAL_TASKS = "create_manual_tasks"
    VIEW_STUDENTS = "view_students"
    MANAGE_ENROLLMENTS = "manage_enrollments"
    TRANSFER_STUDENTS = "transfer_students"
    VIEW_ACHIEVEMENTS = "view_achievements"
    VIEW_OWN_DASHBOARD = "view_own_dashboard"
    VIEW_OWN_TASKS = "view_own_tasks"


ROLE_PERMISSIONS = {
    "student": {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_OWN_ACHIEVEMENTS,
        Permission.VIEW_STUDENT_TASKS,
        Permission.VIEW_OWN_DASHBOARD,
        Permission.VIEW_OWN_TASKS,
        Permission.VIEW_OWN_ACHIEVEMENTS,
    },
    "teacher": {
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_TASKS,
        Permission.MANAGE_ACHIEVEMENTS,
        Permission.UPLOAD_MEDIA,
        Permission.VIEW_ASSESSMENT,
        Permission.VIEW_GROUPS,
        Permission.VIEW_PROGRAMS,
        Permission.CREATE_PROGRAMS,
        Permission.EDIT_PROGRAMS,
        Permission.PUBLISH_PROGRAMS,
        Permission.CREATE_BLOCKS,
        Permission.EDIT_BLOCKS,
        Permission.PUBLISH_BLOCKS,
        Permission.CREATE_TASKS,
        Permission.GRADE_TASKS,
        Permission.CREATE_MANUAL_TASKS,
        Permission.VIEW_STUDENTS,
        Permission.VIEW_ACHIEVEMENTS,
    },
    "assistant": {
        Permission.VIEW_STUDENTS,
        Permission.GRADE_TASKS,
        Permission.VIEW_ACHIEVEMENTS,
    },
    "admin": {
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_TASKS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ACHIEVEMENTS,
        Permission.UPLOAD_MEDIA,
        Permission.VIEW_ASSESSMENT,
        Permission.VIEW_GROUPS,
        Permission.MANAGE_GROUPS,
        Permission.VIEW_PROGRAMS,
        Permission.CREATE_PROGRAMS,
        Permission.EDIT_PROGRAMS,
        Permission.PUBLISH_PROGRAMS,
        Permission.CREATE_BLOCKS,
        Permission.EDIT_BLOCKS,
        Permission.PUBLISH_BLOCKS,
        Permission.CREATE_TASKS,
        Permission.GRADE_TASKS,
        Permission.CREATE_MANUAL_TASKS,
        Permission.VIEW_STUDENTS,
        Permission.MANAGE_ENROLLMENTS,
        Permission.TRANSFER_STUDENTS,
        Permission.VIEW_ACHIEVEMENTS,
        Permission.VIEW_OWN_DASHBOARD,
        Permission.VIEW_OWN_TASKS,
        Permission.VIEW_OWN_ACHIEVEMENTS,
    },
}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def get_access_context(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AccessContext:
    try:
        from core.access_service import access_service
        return access_service.build_context(payload, db)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication payload")


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


def has_permission(user: dict | AccessContext, permission: str, db: Optional[Session] = None) -> bool:
    if not user:
        return False

    if isinstance(user, AccessContext):
        return user.has_permission(permission)

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
        ctx: AccessContext = Depends(get_access_context)
    ):
        if not ctx.has_permission(permission):
            raise HTTPException(status_code=403, detail=f"Access denied: {permission} permission required")
        return ctx

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

require_view_groups = require_permission(Permission.VIEW_GROUPS)
require_manage_groups = require_permission(Permission.MANAGE_GROUPS)
require_view_programs = require_permission(Permission.VIEW_PROGRAMS)
require_create_programs = require_permission(Permission.CREATE_PROGRAMS)
require_edit_programs = require_permission(Permission.EDIT_PROGRAMS)
require_publish_programs = require_permission(Permission.PUBLISH_PROGRAMS)
require_create_blocks = require_permission(Permission.CREATE_BLOCKS)
require_edit_blocks = require_permission(Permission.EDIT_BLOCKS)
require_publish_blocks = require_permission(Permission.PUBLISH_BLOCKS)
require_create_tasks = require_permission(Permission.CREATE_TASKS)
require_grade_tasks = require_permission(Permission.GRADE_TASKS)
require_create_manual_tasks = require_permission(Permission.CREATE_MANUAL_TASKS)
require_view_students = require_permission(Permission.VIEW_STUDENTS)
require_manage_enrollments = require_permission(Permission.MANAGE_ENROLLMENTS)
require_transfer_students = require_permission(Permission.TRANSFER_STUDENTS)
require_view_achievements = require_permission(Permission.VIEW_ACHIEVEMENTS)
require_view_own_dashboard = require_permission(Permission.VIEW_OWN_DASHBOARD)
require_view_own_tasks = require_permission(Permission.VIEW_OWN_TASKS)
