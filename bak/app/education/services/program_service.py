from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import BlockNotFound, PermissionDenied
from education.repositories.program_repository import program_repository
from education.services.program_creation_service import program_creation_service
from education.services.program_read_service import program_read_service
from shared.unit_of_work import UnitOfWork


class ProgramService:
    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        return program_creation_service.create_program(db, ctx=ctx, title=title, description=description)

    def get_programs_for_user(self, db: Session, *, ctx: AccessContext):
        return program_read_service.get_programs_for_user(db, ctx=ctx)

    def get_program_by_id(self, db: Session, *, ctx: AccessContext, program_id: int):
        return program_read_service.get_program_by_id(db, ctx=ctx, program_id=program_id)

    def update_program(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None):
        with UnitOfWork(db):
            program = program_read_service.ensure_program_access(db, ctx=ctx, program_id=program_id)
            program.title = title
            program.description = description
            return program_repository.update(db, program)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        return program_creation_service.create_block(db, ctx=ctx, program_id=program_id, title=title, description=description, order=order)

    def create_topic(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        return program_creation_service.create_topic(db, ctx=ctx, block_id=block_id, title=title, description=description, order=order)

    def publish_block(self, db: Session, *, ctx: AccessContext, block_id: int):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block:
                raise BlockNotFound("Block not found")
            try:
                program_read_service.ensure_program_access(db, ctx=ctx, program_id=block.program_id)
            except PermissionDenied as exc:
                raise PermissionDenied("Access denied to publish block") from exc
            block.status = "published"
            db.flush()
            db.refresh(block)
            return block

    def create_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int | None, title: str, description: str | None, max_score: int, is_manual: bool):
        return program_creation_service.create_task(
            db,
            ctx=ctx,
            block_id=block_id,
            topic_id=topic_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )

    async def add_topic_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, topic_id: int, file):
        return await program_creation_service.add_topic_material(
            db,
            ctx=ctx,
            program_id=program_id,
            block_id=block_id,
            topic_id=topic_id,
            file=file,
        )

    async def add_task_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, task_id: int, file):
        return await program_creation_service.add_task_material(
            db,
            ctx=ctx,
            program_id=program_id,
            block_id=block_id,
            task_id=task_id,
            file=file,
        )

    def delete_material(self, db: Session, *, ctx: AccessContext, program_id: int, material_id: int):
        return program_creation_service.delete_material(db, ctx=ctx, program_id=program_id, material_id=material_id)

    def update_block(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        return program_creation_service.update_block(db, ctx=ctx, block_id=block_id, title=title, description=description, order=order)

    def update_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, title: str, description: str | None, order: int):
        return program_creation_service.update_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id, title=title, description=description, order=order)

    def update_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int, title: str, description: str | None, max_score: int, is_manual: bool, order: int):
        return program_creation_service.update_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id, title=title, description=description, max_score=max_score, is_manual=is_manual, order=order)

    def delete_block(self, db: Session, *, ctx: AccessContext, block_id: int):
        return program_creation_service.delete_block(db, ctx=ctx, block_id=block_id)

    def delete_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int):
        return program_creation_service.delete_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id)

    def delete_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int):
        return program_creation_service.delete_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id)

    def get_program_blocks(self, db: Session, *, program_id: int):
        return program_repository.list_blocks(db, program_id=program_id)


program_service = ProgramService()
