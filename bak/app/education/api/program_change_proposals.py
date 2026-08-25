from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.http import translate_domain_error
from core.permissions import require_view_programs
from db.database import get_db
from education.dtos.program_change_dto import proposal_payload
from education.exceptions.domain_exceptions import EducationError
from education.facade import education_facade
from education.schemas.education import ProgramChangeDecision, ProgramChangeProposalCreate

router = APIRouter(prefix="/program-change-proposals", tags=["education-program-proposals"])
admin_router = APIRouter(prefix="/admin/program-change-proposals", tags=["education-admin-proposals"])


@router.post("/programs/{program_id}", status_code=201)
def create_proposal(
    program_id: int,
    data: ProgramChangeProposalCreate,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposal = education_facade.create_program_change_proposal(
            db,
            ctx=ctx,
            program_id=program_id,
            blocks=[block.model_dump() for block in data.blocks],
            comment=data.comment,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Program change proposal submitted", "data": proposal_payload(proposal)}


@router.get("/my")
def list_my_proposals(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    proposals = education_facade.list_my_program_change_proposals(db, ctx=ctx)
    return {"data": [proposal_payload(proposal) for proposal in proposals]}


@router.get("/{proposal_id}")
def get_my_proposal(
    proposal_id: int,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposal = education_facade.get_program_change_proposal(db, ctx=ctx, proposal_id=proposal_id)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"data": proposal_payload(proposal)}


@admin_router.get("")
def list_admin_proposals(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposals = education_facade.list_program_change_proposals(db, ctx=ctx)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"data": [proposal_payload(proposal) for proposal in proposals]}


@admin_router.get("/{proposal_id}")
def get_admin_proposal(
    proposal_id: int,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposal = education_facade.get_program_change_proposal(db, ctx=ctx, proposal_id=proposal_id)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"data": proposal_payload(proposal)}


@admin_router.post("/{proposal_id}/approve")
def approve_proposal(
    proposal_id: int,
    data: ProgramChangeDecision,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposal = education_facade.approve_program_change_proposal(db, ctx=ctx, proposal_id=proposal_id, comment=data.comment)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Program change proposal approved", "data": proposal_payload(proposal)}


@admin_router.post("/{proposal_id}/reject")
def reject_proposal(
    proposal_id: int,
    data: ProgramChangeDecision,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        proposal = education_facade.reject_program_change_proposal(db, ctx=ctx, proposal_id=proposal_id, comment=data.comment)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Program change proposal rejected", "data": proposal_payload(proposal)}