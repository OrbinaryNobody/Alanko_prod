from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.permissions import get_current_user
from db.database import get_db
from schemas.education import EnrollmentCreate, GradeUpdate, GroupCreate, GroupMemberCreate, ManualTaskCreate, ProgramBlockCreate, ProgramCreate, ProgramTaskCreate
from services.group_service import group_service
from services.program_service import program_service
from services.enrollment_service import enrollment_service
from services.student_task_service import student_task_service
from .common import get_current_teacher_or_admin

router = APIRouter(prefix="/teacher", tags=["teacher-education"])


def require_teacher(user_id: int = Depends(get_current_teacher_or_admin)):
    return user_id


@router.post("/programs")
def create_program(data: ProgramCreate, teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    program = program_service.create_program(db, title=data.title, description=data.description, created_by=teacher_id)
    return {"message": "Program created", "data": {"id": program.id, "title": program.title, "status": program.status}}


@router.get("/programs")
def list_programs(teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    programs = program_service.get_programs_for_user(db, teacher_id)
    return {"data": [{"id": p.id, "title": p.title, "description": p.description, "status": p.status} for p in programs]}


@router.post("/programs/{program_id}/blocks")
def create_block(program_id: int, data: ProgramBlockCreate, current_user: dict = Depends(get_current_user), teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    block = program_service.create_block(db, program_id=program_id, title=data.title, description=data.description, order=data.order, user_id=teacher_id, is_admin=(current_user.get("role") == "admin"))
    return {"message": "Block created", "data": {"id": block.id, "title": block.title, "order": block.order}}


@router.post("/blocks/{block_id}/tasks")
def create_task(block_id: int, data: ProgramTaskCreate, current_user: dict = Depends(get_current_user), teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    task = program_service.create_task(db, block_id=block_id, title=data.title, description=data.description, max_score=data.max_score, is_manual=data.is_manual, user_id=teacher_id, is_admin=(current_user.get("role") == "admin"))
    return {"message": "Task created", "data": {"id": task.id, "title": task.title, "max_score": task.max_score}}


@router.post("/groups")
def create_group(data: GroupCreate, teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    group = group_service.create_group(db, title=data.title, description=data.description, program_id=data.program_id, created_by=teacher_id)
    return {"message": "Group created", "data": {"id": group.id, "title": group.title}}


@router.get("/groups")
def list_groups(teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    groups = group_service.get_groups_for_user(db, teacher_id)
    return {"data": [{"id": g.id, "title": g.title, "program_id": g.program_id, "status": g.status} for g in groups]}


@router.post("/groups/{group_id}/members")
def add_member(group_id: int, data: GroupMemberCreate, current_user: dict = Depends(get_current_user), teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    member = group_service.add_member(db, group_id=group_id, user_id=data.user_id, role=data.role, actor_id=teacher_id, is_admin=(current_user.get("role") == "admin"))
    return {"message": "Member added", "data": {"group_id": group_id, "user_id": member.user_id, "role": member.role}}


@router.post("/groups/{group_id}/enrollments")
def enroll_student(group_id: int, data: EnrollmentCreate, current_user: dict = Depends(get_current_user), teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    enrollment = group_service.enroll_student(db, group_id=group_id, student_id=data.student_id, actor_id=teacher_id, is_admin=(current_user.get("role") == "admin"))
    return {"message": "Student enrolled", "data": {"id": enrollment.id, "student_id": enrollment.student_id}}


@router.post("/manual-tasks")
def create_manual_task(data: ManualTaskCreate, teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    task = student_task_service.create_manual_task(db, enrollment_id=data.enrollment_id, program_task_id=data.program_task_id)
    return {"message": "Manual task created", "data": {"id": task.id, "status": task.status}}


@router.put("/student-tasks/{task_id}/grade")
def update_grade(task_id: int, data: GradeUpdate, teacher_id: int = Depends(require_teacher), db: Session = Depends(get_db)):
    task = student_task_service.update_task_grade(db, task_id=task_id, grade=data.grade, feedback=data.feedback)
    return {"message": "Grade updated", "data": {"id": task.id, "grade": task.grade, "feedback": task.feedback}}
