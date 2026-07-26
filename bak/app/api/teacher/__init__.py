from fastapi import APIRouter

from .achievements import router as achievements_router
from .categories import router as categories_router
from .students import router as students_router
from .tasks import router as tasks_router

router = APIRouter()

router.include_router(students_router)
router.include_router(tasks_router)
router.include_router(categories_router)
router.include_router(achievements_router)
