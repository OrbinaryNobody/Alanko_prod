from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.task import CategoryCreate
from services.data_access import teacher_service

from .common import get_current_teacher_or_admin

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.post("/create-category")
def create_category(
    data: CategoryCreate,
    user_id: int = Depends(get_current_teacher_or_admin),
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
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    categories = teacher_service.get_categories(db)
    return {
        "data": [
            {"id": category.id, "name": category.name, "description": category.description}
            for category in categories
        ]
    }
