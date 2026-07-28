from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import (
    require_create_blocks,
    require_create_manual_tasks,
    require_create_programs,
    require_create_tasks,
    require_edit_programs,
    require_grade_tasks,
    require_publish_blocks,
    require_view_groups,
    require_view_programs,
    require_view_students,
)
from db.database import get_db
from schemas.education import GradeUpdate, ManualTaskCreate, ProgramBlockCreate, ProgramCreate, ProgramTaskCreate
from services.group_service import group_service
from services.program_service import program_service
from services.student_task_service import student_task_service

router = APIRouter(prefix="/teacher", tags=["teacher-education"])


@router.post("/programs")
def create_program(data: ProgramCreate, ctx: AccessContext = Depends(require_create_programs), db: Session = Depends(get_db)):
    program = program_service.create_program(db, title=data.title, description=data.description, created_by=ctx.user_id)
    return {"message": "Program created", "data": {"id": program.id, "title": program.title, "status": program.status}}


@router.get("/programs")
def list_programs(ctx: AccessContext = Depends(require_view_programs), db: Session = Depends(get_db)):
    programs = program_service.get_programs_for_user(db, ctx.user_id, is_admin=ctx.is_admin)
    return {"data": [{"id": p.id, "title": p.title, "description": p.description, "status": p.status} for p in programs]}


@router.put("/programs/{program_id}")
def update_program(program_id: int, data: ProgramCreate, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    program = program_service.update_program(db, program_id=program_id, title=data.title, description=data.description, user_id=ctx.user_id, is_admin=ctx.is_admin)
    return {"message": "Program updated", "data": {"id": program.id, "title": program.title, "status": program.status}}


@router.post("/programs/{program_id}/blocks")
def create_block(program_id: int, data: ProgramBlockCreate, ctx: AccessContext = Depends(require_create_blocks), db: Session = Depends(get_db)):
    block = program_service.create_block(db, program_id=program_id, title=data.title, description=data.description, order=data.order, user_id=ctx.user_id, is_admin=ctx.is_admin)
    return {"message": "Block created", "data": {"id": block.id, "title": block.title, "order": block.order}}


@router.post("/blocks/{block_id}/tasks")
def create_task(block_id: int, data: ProgramTaskCreate, ctx: AccessContext = Depends(require_create_tasks), db: Session = Depends(get_db)):
    task = program_service.create_task(db, block_id=block_id, title=data.title, description=data.description, max_score=data.max_score, is_manual=data.is_manual, user_id=ctx.user_id, is_admin=ctx.is_admin)
    return {"message": "Task created", "data": {"id": task.id, "title": task.title, "max_score": task.max_score}}


@router.patch("/blocks/{block_id}/publish")
def publish_block(block_id: int, ctx: AccessContext = Depends(require_publish_blocks), db: Session = Depends(get_db)):
    block = program_service.publish_block(db, block_id=block_id, user_id=ctx.user_id, is_admin=ctx.is_admin)
    return {"message": "Block published", "data": {"id": block.id, "status": block.status}}


@router.get("/groups")
def list_groups(ctx: AccessContext = Depends(require_view_groups), db: Session = Depends(get_db)):
    groups = group_service.get_groups_for_user(db, ctx.user_id, is_admin=ctx.is_admin)
    return {"data": [{"id": g.id, "title": g.title, "program_id": g.program_id, "status": g.status} for g in groups]}


@router.get("/groups/{group_id}/students")
def get_group_students(group_id: int, ctx: AccessContext = Depends(require_view_students), db: Session = Depends(get_db)):
    students = group_service.get_group_students(db, group_id=group_id, actor_id=ctx.user_id, is_admin=ctx.is_admin)
    return {"data": students}


@router.post("/manual-tasks")
def create_manual_task(data: ManualTaskCreate, ctx: AccessContext = Depends(require_create_manual_tasks), db: Session = Depends(get_db)):
    task = student_task_service.create_manual_task(db, ctx, enrollment_id=data.enrollment_id, program_task_id=data.program_task_id)
    return {"message": "Manual task created", "data": {"id": task.id, "status": task.status}}


@router.put("/student-tasks/{task_id}")
def update_grade(task_id: int, data: GradeUpdate, ctx: AccessContext = Depends(require_grade_tasks), db: Session = Depends(get_db)):
    task = student_task_service.update_task_grade(db, ctx, task_id=task_id, grade=data.grade, feedback=data.feedback)
    return {"message": "Grade updated", "data": {"id": task.id, "grade": task.grade, "feedback": task.feedback}}
