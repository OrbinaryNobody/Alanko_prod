from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from db.database import get_db
from schemas.task import TaskCreate, TaskUpdate
from services.data_access import teacher_service

from core.permissions import require_create_tasks, require_edit_programs

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.post("/create-task")
def create_task(
    data: TaskCreate,
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db)
):
    task, students_count = teacher_service.create_task(db, data=data)

    return {
        "message": "task created and assigned",
        "task_id": task.id,
        "students_count": students_count
    }


@router.get("/tasks")
def get_tasks(
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db)
):
    tasks = teacher_service.get_tasks(db)

    return {
        "data": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "category_id": task.category_id,
                "category_name": task.category.name if task.category else None,
                "difficulty": task.difficulty,
                "max_score": task.max_score,
                "deadline": None
            }
            for task in tasks
        ]
    }


@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db)
):
    task = teacher_service.update_task(db, task_id=task_id, task_data=task_data)

    return {
        "message": "Task updated successfully",
        "data": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category_id": task.category_id,
            "category_name": task.category.name if task.category else None,
            "difficulty": task.difficulty,
            "max_score": task.max_score,
            "deadline": None
        }
    }
