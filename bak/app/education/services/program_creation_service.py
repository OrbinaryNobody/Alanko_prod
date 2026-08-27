from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.policies.program_policy import ProgramPolicy
from education.repositories.program_repository import program_repository
from shared.unit_of_work import UnitOfWork


class ProgramCreationService:
    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        if not ctx.is_admin and not ctx.can("create_programs"):
            raise PermissionDenied("Access denied to create program")

        with UnitOfWork(db):
            return program_repository.create(db, title=title, description=description, created_by=ctx.user_id)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        with UnitOfWork(db):
            program = program_repository.get_by_id(db, program_id)
            if not program:
                raise PermissionDenied("Program not found")

            try:
                ProgramPolicy.require_edit_program(ctx, program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc

            return program_repository.create_block(db, program_id=program.id, title=title, description=description, order=order)

    def create_topic(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block:
                raise PermissionDenied("Block not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            return program_repository.create_topic(db, block_id=block_id, title=title, description=description, order=order)

    def create_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int | None, title: str, description: str | None, max_score: int, is_manual: bool):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block:
                raise PermissionDenied("Block not found")

            program = program_repository.get_by_id(db, block.program_id)
            if not program:
                raise PermissionDenied("Program not found")

            try:
                ProgramPolicy.require_edit_program(ctx, program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc

            if topic_id is not None and not any(topic.id == topic_id for topic in block.topics):
                raise PermissionDenied("Topic does not belong to block")
            return program_repository.create_task(db, block_id=block.id, topic_id=topic_id, title=title, description=description, max_score=max_score, is_manual=is_manual)

    def update_block(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block:
                raise PermissionDenied("Block not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            block.title = title
            block.description = description
            block.order = order
            db.flush()
            db.refresh(block)
            return block

    def update_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, title: str, description: str | None, order: int):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            topic = program_repository.get_topic_by_id(db, topic_id)
            if not block or not topic or topic.block_id != block_id:
                raise PermissionDenied("Topic not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            topic.title = title
            topic.description = description
            topic.order = order
            db.flush()
            db.refresh(topic)
            return topic

    def update_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int, title: str, description: str | None, max_score: int, is_manual: bool, order: int):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            task = program_repository.get_task_by_id(db, task_id)
            if not block or not task or task.block_id != block_id or task.topic_id != topic_id:
                raise PermissionDenied("Task not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            task.title = title
            task.description = description
            task.max_score = max_score
            task.is_manual = is_manual
            task.order = order
            db.flush()
            db.refresh(task)
            return task

    def delete_block(self, db: Session, *, ctx: AccessContext, block_id: int) -> None:
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block:
                raise PermissionDenied("Block not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            program_repository.delete_block(db, block)

    def delete_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int) -> None:
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            topic = program_repository.get_topic_by_id(db, topic_id)
            if not block or not topic or topic.block_id != block_id:
                raise PermissionDenied("Topic not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            program_repository.delete_topic(db, topic)

    def delete_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int) -> None:
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            task = program_repository.get_task_by_id(db, task_id)
            if not block or not task or task.block_id != block_id or task.topic_id != topic_id:
                raise PermissionDenied("Task not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc
            program_repository.delete_task(db, task)


program_creation_service = ProgramCreationService()
