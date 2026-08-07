from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from assessment.facade import assessment_facade
from core.access import AccessContext
from core.permissions import require_view_students
from db.database import get_db

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/student/{student_id}/task/{task_id}")
def get_task_assessment(
    student_id: int,
    task_id: int,
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db),
):
    return assessment_facade.get_assessment_payload(db, ctx=ctx, student_id=student_id, task_id=task_id)
