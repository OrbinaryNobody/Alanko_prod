from models import Achievement, UserAchievement

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.access import AccessContext
from db.database import get_db
from services.auth_service import auth_service
from services.program_service import program_service
from services.group_service import group_service
from schemas.auth import AdminAddUserSchema
from schemas.education import GroupCreate, GroupMemberCreate, ProgramBlockCreate, ProgramCreate, ProgramTaskCreate, EnrollmentCreate
from core.access import AccessContext
from core.access import AccessContext
from core.permissions import Permission, get_current_user, get_access_context, has_permission, require_manage_groups, require_manage_enrollments, require_create_programs, require_create_blocks, require_create_tasks, require_manage_users

router = APIRouter(prefix="/admin", tags=["admin"])


# =========================
# Зависимость для проверки доступа администратора
# =========================
def get_current_admin(ctx: AccessContext = Depends(get_access_context), db: Session = Depends(get_db)):
    if not ctx or not ctx.user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not any(
        ctx.has_permission(perm)
        for perm in (
            Permission.MANAGE_USERS,
            Permission.MANAGE_GROUPS,
            Permission.CREATE_PROGRAMS,
        )
    ):
        raise HTTPException(status_code=403, detail="Access denied: Admin permissions required")
    return ctx.user_id


# =========================
# Добавление пользователя админом
# =========================
@router.post("/add-user")
def add_user(
    data: AdminAddUserSchema,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db)
):
    try:
        user = auth_service.add_user_by_admin(db, data)
        return {
            "message": f"User added successfully with role '{data.role}'",
            "user_id": user.id,
            "email": user.email,
            "password": user.plain_password if getattr(user, 'plain_password', None) else None
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/programs")
def create_program(
    data: ProgramCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_create_programs),
    db: Session = Depends(get_db)
):
    program = program_service.create_program(db, title=data.title, description=data.description, created_by=admin_id)
    return {"message": "Program created", "data": {"id": program.id, "title": program.title, "status": program.status}}


@router.post("/programs/{program_id}/blocks")
def create_block(
    program_id: int,
    data: ProgramBlockCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_create_blocks),
    db: Session = Depends(get_db)
):
    block = program_service.create_block(db, program_id=program_id, title=data.title, description=data.description, order=data.order, user_id=admin_id, is_admin=True)
    return {"message": "Block created", "data": {"id": block.id, "title": block.title, "order": block.order}}


@router.post("/blocks/{block_id}/tasks")
def create_task(
    block_id: int,
    data: ProgramTaskCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db)
):
    task = program_service.create_task(db, block_id=block_id, title=data.title, description=data.description, max_score=data.max_score, is_manual=data.is_manual, user_id=admin_id, is_admin=True)
    return {"message": "Task created", "data": {"id": task.id, "title": task.title, "max_score": task.max_score}}


@router.post("/groups")
def create_group(
    data: GroupCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db)
):
    group = group_service.create_group(db, title=data.title, description=data.description, program_id=data.program_id, created_by=admin_id)
    return {"message": "Group created", "data": {"id": group.id, "title": group.title}}


@router.post("/groups/{group_id}/members")
def add_member(
    group_id: int,
    data: GroupMemberCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db)
):
    member = group_service.add_member(db, group_id=group_id, user_id=data.user_id, role=data.role, actor_id=admin_id, is_admin=True)
    return {"message": "Member added", "data": {"group_id": group_id, "user_id": member.user_id, "role": member.role}}


@router.post("/groups/{group_id}/enrollments")
def enroll_student(
    group_id: int,
    data: EnrollmentCreate,
    admin_id: int = Depends(get_current_admin),
    ctx: AccessContext = Depends(require_manage_enrollments),
    db: Session = Depends(get_db)
):
    enrollment = group_service.enroll_student(db, group_id=group_id, student_id=data.student_id, actor_id=admin_id, is_admin=True)
    return {"message": "Student enrolled", "data": {"id": enrollment.id, "student_id": enrollment.student_id}}


