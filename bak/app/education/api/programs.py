from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.http import translate_domain_error
from core.permissions import (
    require_create_blocks,
    require_create_programs,
    require_edit_programs,
    require_view_programs,
)
from db.database import get_db
from education.dtos.program_dto import BlockPayload, ProgramPayload
from education.exceptions.domain_exceptions import EducationError
from education.facade import education_facade
from education.schemas.education import ProgramBlockCreate, ProgramBlockUpdate, ProgramCreate, ProgramTaskCreate, ProgramTaskUpdate, ProgramTopicCreate, ProgramTopicUpdate

router = APIRouter(prefix="/programs", tags=["education-programs"])


def _program_to_payload(program):
    return ProgramPayload(program.id, program.title, program.description, program.status).to_dict()


def _block_to_payload(block):
    return BlockPayload(block.id, block.title, block.order, block.status).to_dict()


def _material_to_payload(material):
    return {
        "id": material.id,
        "file_name": material.file_name,
        "content_type": material.content_type,
        "file_url": material.file_url,
    }


@router.post("", status_code=201)
def create_program(
    data: ProgramCreate,
    ctx: AccessContext = Depends(require_create_programs),
    db: Session = Depends(get_db),
):
    try:
        program = education_facade.create_program(
            db,
            ctx=ctx,
            title=data.title,
            description=data.description,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Program created", "data": _program_to_payload(program)}


@router.get("")
def list_programs(
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    programs = education_facade.get_programs_for_user(db, ctx=ctx)
    return {"data": [_program_to_payload(program) for program in programs]}


@router.get("/{program_id}/structure")
def get_program_structure(
    program_id: int,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        program = education_facade.get_program_by_id(db, ctx=ctx, program_id=program_id)
    except EducationError as exc:
        translate_domain_error(exc)
    return {
        "data": {
            **_program_to_payload(program),
            "blocks": [
                {
                    "id": block.id,
                    "title": block.title,
                    "description": block.description,
                    "order": block.order,
                    "status": block.status,
                    "topics": [
                        {
                            "id": topic.id,
                            "title": topic.title,
                            "description": topic.description,
                            "order": topic.order,
                            "status": topic.status,
                            "materials": [_material_to_payload(material) for material in topic.materials],
                            "tasks": [
                                {
                                    "id": task.id,
                                    "title": task.title,
                                    "description": task.description,
                                    "max_score": task.max_score,
                                    "order": task.order,
                                    "is_manual": task.is_manual,
                                    "materials": [_material_to_payload(material) for material in task.materials],
                                }
                                for task in topic.tasks
                            ],
                        }
                        for topic in block.topics
                    ],
                }
                for block in sorted(program.blocks, key=lambda item: (item.order, item.id))
            ],
        }
    }


@router.get("/{program_id}")
def get_program(
    program_id: int,
    ctx: AccessContext = Depends(require_view_programs),
    db: Session = Depends(get_db),
):
    try:
        program = education_facade.get_program_by_id(db, ctx=ctx, program_id=program_id)
    except EducationError as exc:
        translate_domain_error(exc)

    return {"data": _program_to_payload(program)}


@router.put("/{program_id}")
def update_program(
    program_id: int,
    data: ProgramCreate,
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db),
):
    try:
        program = education_facade.update_program(
            db,
            ctx=ctx,
            program_id=program_id,
            title=data.title,
            description=data.description,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Program updated", "data": _program_to_payload(program)}


@router.post("/{program_id}/blocks", status_code=201)
def create_block(
    program_id: int,
    data: ProgramBlockCreate,
    ctx: AccessContext = Depends(require_create_blocks),
    db: Session = Depends(get_db),
):
    try:
        block = education_facade.create_block(
            db,
            ctx=ctx,
            program_id=program_id,
            title=data.title,
            description=data.description,
            order=data.order,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Block created", "data": _block_to_payload(block)}


@router.post("/blocks/{block_id}/topics", status_code=201)
def create_topic(
    block_id: int,
    data: ProgramTopicCreate,
    ctx: AccessContext = Depends(require_create_blocks),
    db: Session = Depends(get_db),
):
    try:
        topic = education_facade.create_topic(
            db,
            ctx=ctx,
            block_id=block_id,
            title=data.title,
            description=data.description,
            order=data.order,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Topic created", "data": {"id": topic.id, "block_id": topic.block_id, "title": topic.title, "description": topic.description, "order": topic.order}}


@router.post("/blocks/{block_id}/topics/{topic_id}/tasks", status_code=201)
def create_topic_task(
    block_id: int,
    topic_id: int,
    data: ProgramTaskCreate,
    ctx: AccessContext = Depends(require_create_blocks),
    db: Session = Depends(get_db),
):
    try:
        task = education_facade.create_task_for_block(
            db,
            ctx=ctx,
            block_id=block_id,
            topic_id=topic_id,
            title=data.title,
            description=data.description,
            max_score=data.max_score,
            is_manual=data.is_manual,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Task created", "data": {"id": task.id, "topic_id": task.topic_id, "title": task.title, "description": task.description, "max_score": task.max_score, "order": task.order}}


@router.post("/{program_id}/blocks/{block_id}/topics/{topic_id}/materials", status_code=201)
async def upload_topic_material(
    program_id: int,
    block_id: int,
    topic_id: int,
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db),
):
    try:
        material = await education_facade.add_topic_material(
            db,
            ctx=ctx,
            program_id=program_id,
            block_id=block_id,
            topic_id=topic_id,
            file=file,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Topic material uploaded", "data": _material_to_payload(material)}


@router.post("/{program_id}/blocks/{block_id}/tasks/{task_id}/materials", status_code=201)
async def upload_task_material(
    program_id: int,
    block_id: int,
    task_id: int,
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db),
):
    try:
        material = await education_facade.add_task_material(
            db,
            ctx=ctx,
            program_id=program_id,
            block_id=block_id,
            task_id=task_id,
            file=file,
        )
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Task material uploaded", "data": _material_to_payload(material)}


@router.delete("/{program_id}/materials/{material_id}", status_code=204)
def delete_program_material(
    program_id: int,
    material_id: int,
    ctx: AccessContext = Depends(require_edit_programs),
    db: Session = Depends(get_db),
):
    try:
        education_facade.delete_program_material(db, ctx=ctx, program_id=program_id, material_id=material_id)
    except EducationError as exc:
        translate_domain_error(exc)


@router.put("/{program_id}/blocks/{block_id}")
def update_block(program_id: int, block_id: int, data: ProgramBlockUpdate, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        program = education_facade.get_program_by_id(db, ctx=ctx, program_id=program_id)
        if not any(item.id == block_id for item in program.blocks):
            translate_domain_error(EducationError("Block does not belong to program"))
        block = education_facade.update_block(db, ctx=ctx, block_id=block_id, title=data.title, description=data.description, order=data.order)
    except EducationError as exc:
        translate_domain_error(exc)
    if block.program_id != program_id:
        translate_domain_error(EducationError("Block does not belong to program"))
    return {"message": "Block updated", "data": _block_to_payload(block)}


@router.delete("/{program_id}/blocks/{block_id}", status_code=204)
def delete_block(program_id: int, block_id: int, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        block = education_facade.get_program_by_id(db, ctx=ctx, program_id=program_id)
        if not any(item.id == block_id for item in block.blocks):
            translate_domain_error(EducationError("Block does not belong to program"))
        education_facade.delete_block(db, ctx=ctx, block_id=block_id)
    except EducationError as exc:
        translate_domain_error(exc)


@router.put("/{program_id}/blocks/{block_id}/topics/{topic_id}")
def update_topic(program_id: int, block_id: int, topic_id: int, data: ProgramTopicUpdate, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        topic = education_facade.update_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id, title=data.title, description=data.description, order=data.order)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Topic updated", "data": {"id": topic.id, "block_id": topic.block_id, "title": topic.title, "description": topic.description, "order": topic.order}}


@router.delete("/{program_id}/blocks/{block_id}/topics/{topic_id}", status_code=204)
def delete_topic(program_id: int, block_id: int, topic_id: int, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        education_facade.delete_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id)
    except EducationError as exc:
        translate_domain_error(exc)


@router.put("/{program_id}/blocks/{block_id}/topics/{topic_id}/tasks/{task_id}")
def update_program_task(program_id: int, block_id: int, topic_id: int, task_id: int, data: ProgramTaskUpdate, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        task = education_facade.update_program_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id, title=data.title, description=data.description, max_score=data.max_score, is_manual=data.is_manual, order=data.order)
    except EducationError as exc:
        translate_domain_error(exc)
    return {"message": "Program task updated", "data": {"id": task.id, "topic_id": task.topic_id, "title": task.title, "description": task.description, "max_score": task.max_score, "order": task.order, "is_manual": task.is_manual}}


@router.delete("/{program_id}/blocks/{block_id}/topics/{topic_id}/tasks/{task_id}", status_code=204)
def delete_program_task(program_id: int, block_id: int, topic_id: int, task_id: int, ctx: AccessContext = Depends(require_edit_programs), db: Session = Depends(get_db)):
    try:
        education_facade.delete_program_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id)
    except EducationError as exc:
        translate_domain_error(exc)
