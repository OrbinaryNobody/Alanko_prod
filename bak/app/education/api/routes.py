from fastapi import APIRouter

from education.api.groups import router as groups_router
from education.api.programs import router as programs_router
from education.api.students import router as students_router
from education.api.tasks import router as tasks_router
from education.api.program_change_proposals import admin_router as program_change_admin_router
from education.api.program_change_proposals import router as program_change_router

router = APIRouter(prefix="/education", tags=["education"])

router.include_router(groups_router, prefix="", tags=["education"])
router.include_router(programs_router, prefix="", tags=["education"])
router.include_router(students_router, prefix="", tags=["education"])
router.include_router(tasks_router, prefix="", tags=["education"])
router.include_router(program_change_router, prefix="", tags=["education"])
router.include_router(program_change_admin_router, prefix="", tags=["education"])