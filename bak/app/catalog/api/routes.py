from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import require_view_programs
from db.database import get_db
from education.dtos.program_dto import ProgramPayload
from education.facade import education_facade

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "catalog"}


@router.get("/programs")
def list_catalog_programs(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    programs = education_facade.get_programs_for_user(db, ctx=ctx)
    return {"data": [ProgramPayload(id=program.id, title=program.title, description=program.description, status=program.status).to_dict() for program in programs]}
