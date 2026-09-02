from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.security import verify_token
from db.database import get_db

security = HTTPBearer()


class Permission:
    MANAGE_ACHIEVEMENTS = "manage_achievements"
    UPLOAD_MEDIA = "upload_media"
    VIEW_OWN_DASHBOARD = "view_own_dashboard"
    VIEW_OWN_TASKS = "view_own_tasks"
    VIEW_OWN_ACHIEVEMENTS = "view_own_achievements"
    VIEW_ASSESSMENT = "view_assessment"
    VIEW_GROUPS = "view_groups"
    MANAGE_GROUPS = "manage_groups"
    VIEW_PROGRAMS = "view_programs"
    CREATE_PROGRAMS = "create_programs"
    EDIT_PROGRAMS = "edit_programs"
    SUGGEST_PROGRAM_CHANGES = "suggest_program_changes"
    CREATE_BLOCKS = "create_blocks"
    CREATE_TASKS = "create_tasks"
    GRADE_TASKS = "grade_tasks"
    CREATE_MANUAL_TASKS = "create_manual_tasks"
    VIEW_STUDENTS = "view_students"
    VIEW_ATTENDANCE = "view_attendance"
    MANAGE_ATTENDANCE = "manage_attendance"
    MANAGE_ENROLLMENTS = "manage_enrollments"
    VIEW_ACHIEVEMENTS = "view_achievements"
    MANAGE_USERS = "manage_users"
    VIEW_CONSULTATIONS = "view_consultations"
    BOOK_CONSULTATIONS = "book_consultations"
    MANAGE_CONSULTATIONS = "manage_consultations"
    MANAGE_NEWS = "manage_news"


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def get_access_context(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccessContext:
    try:
        from core.access_service import access_service
        return access_service.build_context(payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication payload") from exc


def require_permission(permission: str):
    def dependency(ctx: AccessContext = Depends(get_access_context)):
        if not ctx.is_admin and not ctx.can(permission):
            raise HTTPException(status_code=403, detail=f"Access denied: {permission} permission required")
        return ctx

    return dependency


def require_student_consultation_booking():
    def dependency(ctx: AccessContext = Depends(get_access_context)):
        if not ctx.has_role("student"):
            raise HTTPException(
                status_code=403,
                detail="Only students can book consultations",
            )
        return ctx

    return dependency


def require_any_permission(*permissions: str):
    def dependency(ctx: AccessContext = Depends(get_access_context)):
        if not ctx.is_admin and not ctx.can_any(*permissions):
            required = ", ".join(permissions)
            raise HTTPException(status_code=403, detail=f"Access denied: one of [{required}] permissions required")
        return ctx

    return dependency


require_manage_achievements = require_permission(Permission.MANAGE_ACHIEVEMENTS)
require_upload_media = require_permission(Permission.UPLOAD_MEDIA)
require_view_own_dashboard = require_permission(Permission.VIEW_OWN_DASHBOARD)
require_view_own_tasks = require_permission(Permission.VIEW_OWN_TASKS)
require_view_own_achievements = require_permission(Permission.VIEW_OWN_ACHIEVEMENTS)
require_view_assessment = require_permission(Permission.VIEW_ASSESSMENT)
require_view_groups = require_permission(Permission.VIEW_GROUPS)
require_manage_groups = require_permission(Permission.MANAGE_GROUPS)
require_view_programs = require_permission(Permission.VIEW_PROGRAMS)
require_create_programs = require_permission(Permission.CREATE_PROGRAMS)
require_edit_programs = require_permission(Permission.EDIT_PROGRAMS)
require_suggest_program_changes = require_permission(Permission.SUGGEST_PROGRAM_CHANGES)
require_create_blocks = require_permission(Permission.CREATE_BLOCKS)
require_create_tasks = require_permission(Permission.CREATE_TASKS)
require_grade_tasks = require_permission(Permission.GRADE_TASKS)
require_create_manual_tasks = require_permission(Permission.CREATE_MANUAL_TASKS)
require_view_students = require_permission(Permission.VIEW_STUDENTS)
require_view_attendance = require_permission(Permission.VIEW_ATTENDANCE)
require_manage_attendance = require_permission(Permission.MANAGE_ATTENDANCE)
require_manage_enrollments = require_permission(Permission.MANAGE_ENROLLMENTS)
require_view_achievements = require_permission(Permission.VIEW_ACHIEVEMENTS)
require_publish_blocks = require_permission(Permission.CREATE_BLOCKS)
require_manage_users = require_permission(Permission.MANAGE_USERS)
require_view_consultations = require_permission(Permission.VIEW_CONSULTATIONS)
require_book_consultations = require_permission(Permission.BOOK_CONSULTATIONS)
require_manage_consultations = require_permission(Permission.MANAGE_CONSULTATIONS)
require_manage_news = require_permission(Permission.MANAGE_NEWS)
