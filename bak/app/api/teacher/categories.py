from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from db.database import get_db
from schemas.task import CategoryCreate
from services.data_access import teacher_service

from core.permissions import require_create_tasks, require_view_programs

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.post("/create-category")
def create_category(
    data: CategoryCreate,
    ctx: AccessContext = Depends(require_create_tasks),
    db: Session = Depends(get_db)
):
    category = teacher_service.create_category(
        db,
        name=data.name,
        description=data.description,
    )

    return {
        "message": "Category created successfully",
        "category_id": category.id,
        "name": category.name
    }


@router.get("/categories")
def get_categories(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db)
):
    categories = teacher_service.get_categories(db)
    return {
        "data": [
            {"id": category.id, "name": category.name, "description": category.description}
            for category in categories
        ]
    }
