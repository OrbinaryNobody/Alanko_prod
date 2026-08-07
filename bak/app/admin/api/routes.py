from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from admin.dtos.admin_dto import (
    BlockCreatePayload,
    EnrollmentCreatePayload,
    GroupCreatePayload,
    MemberAddPayload,
    ProgramCreatePayload,
    TaskCreatePayload,
    UserCreatePayload,
)
from admin.facade import admin_facade
from core.access import AccessContext
from core.permissions import (
    Permission,
    require_any_permission,
    require_manage_users,
)
from db.database import get_db
from schemas.auth import AdminAddUserSchema
from schemas.education import EnrollmentCreate, GroupCreate, GroupMemberCreate, ProgramBlockCreate, ProgramCreate, ProgramTaskCreate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", status_code=201)
def add_user(
    data: AdminAddUserSchema,
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    user = admin_facade.add_user_by_admin(db, data=data)

    return {
        "message": f"User added successfully with role '{data.role}'",
        "data": UserCreatePayload(
            user_id=user.id,
            email=user.email,
            password=user.plain_password if getattr(user, 'plain_password', None) else None,
        ).to_dict(),
    }


@router.post("/programs", status_code=201)
def create_program(
    data: ProgramCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.CREATE_PROGRAMS, Permission.MANAGE_GROUPS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    program = admin_facade.create_program(
        db,
        ctx=ctx,
        title=data.title,
        description=data.description,
    )
    return {"message": "Program created", "data": ProgramCreatePayload(id=program.id, title=program.title, status=program.status, description=program.description).to_dict()}


@router.post("/programs/{program_id}/blocks", status_code=201)
def create_block(
    program_id: int,
    data: ProgramBlockCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.CREATE_PROGRAMS, Permission.MANAGE_GROUPS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    block = admin_facade.create_block(
        db,
        ctx=ctx,
        program_id=program_id,
        title=data.title,
        description=data.description,
        order=data.order,
    )
    return {"message": "Block created", "data": BlockCreatePayload(id=block.id, title=block.title, order=block.order).to_dict()}


@router.post("/blocks/{block_id}/tasks", status_code=201)
def create_task(
    block_id: int,
    data: ProgramTaskCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.CREATE_PROGRAMS, Permission.MANAGE_GROUPS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    task = admin_facade.create_task(
        db,
        ctx=ctx,
        block_id=block_id,
        title=data.title,
        description=data.description,
        max_score=data.max_score,
        is_manual=data.is_manual,
    )
    return {"message": "Task created", "data": TaskCreatePayload(id=task.id, title=task.title, max_score=task.max_score).to_dict()}


@router.post("/groups", status_code=201)
def create_group(
    data: GroupCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_GROUPS, Permission.MANAGE_USERS, Permission.CREATE_PROGRAMS)),
    db: Session = Depends(get_db),
):
    group = admin_facade.create_group(
        db,
        ctx=ctx,
        title=data.title,
        description=data.description,
        program_id=data.program_id,
    )
    return {"message": "Group created", "data": GroupCreatePayload(id=group.id, title=group.title).to_dict()}


@router.post("/groups/{group_id}/members", status_code=201)
def add_member(
    group_id: int,
    data: GroupMemberCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_GROUPS, Permission.MANAGE_USERS, Permission.CREATE_PROGRAMS)),
    db: Session = Depends(get_db),
):
    member = admin_facade.add_member(
        db,
        ctx=ctx,
        group_id=group_id,
        user_id=data.user_id,
        role=data.role,
    )
    return {"message": "Member added", "data": MemberAddPayload(group_id=group_id, user_id=member.user_id, role=member.role).to_dict()}


@router.post("/groups/{group_id}/enrollments", status_code=201)
def enroll_student(
    group_id: int,
    data: EnrollmentCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_ENROLLMENTS, Permission.MANAGE_GROUPS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    enrollment = admin_facade.enroll_student(
        db,
        ctx=ctx,
        group_id=group_id,
        student_id=data.student_id,
    )
    return {"message": "Student enrolled", "data": EnrollmentCreatePayload(id=enrollment.id, student_id=enrollment.student_id).to_dict()}
