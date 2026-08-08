from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.http import translate_domain_error
from core.permissions import require_create_tasks, require_edit_programs, require_view_programs
from db.database import get_db
from education.dtos.program_dto import TaskPayload
from education.exceptions.domain_exceptions import EducationError
from education.facade import education_facade
from schemas.task import CategoryCreate, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["education-tasks"])


def _task_to_payload(task):
    return TaskPayload(
        id=task.id,
        title=task.title,
        description=task.description,
        category_id=task.category_id,
        category_name=task.category.name if task.category else None,
        difficulty=task.difficulty,
        max_score=task.max_score,
        deadline=None,
    ).to_dict()


@router.post("", status_code=201)
def create_task(
    data: TaskCreate,
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db),
):
    try:
        task, students_count = education_facade.create_task(
            db,
            ctx=ctx,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            difficulty=data.difficulty,
            max_score=data.max_score,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {
        "message": "Task created and assigned",
        "task": _task_to_payload(task),
        "students_count": students_count,
    }


@router.get("")
def get_tasks(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    tasks = education_facade.get_tasks(db, ctx=ctx)
    return {"data": [_task_to_payload(task) for task in tasks]}


@router.get("/categories")
def get_categories(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    categories = education_facade.get_categories(db)
    return {"data": [{"id": category.id, "name": category.name, "description": category.description} for category in categories]}


@router.post("/categories", status_code=201)
def create_category(
    data: CategoryCreate,
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db),
):
    category = education_facade.create_category(db, ctx=ctx, name=data.name, description=data.description)
    return {"message": "Category created", "data": {"id": category.id, "name": category.name, "description": category.description}}


@router.get("/{task_id}")
def get_task_detail(
    task_id: int,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        task = education_facade.get_task(db, ctx=ctx, task_id=task_id)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"data": _task_to_payload(task)}


@router.put("/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db),
):
    try:
        task = education_facade.update_task(db, ctx=ctx, task_id=task_id, task_data=task_data)
    except EducationError as exc:
        translate_domain_error(exc)
    return {
        "message": "Task updated successfully",
        "data": _task_to_payload(task),
    }
