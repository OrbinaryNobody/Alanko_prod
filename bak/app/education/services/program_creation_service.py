from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.policies.program_policy import ProgramPolicy
from education.repositories.program_repository import program_repository
from db.minio_client import BUCKET_NAMES
from infrastructure.storage.file_service import file_service
from models.domains.education import Group, GroupEnrollment, GroupStudentTask, ProgramMaterial, ProgramTask, ProgramTopic
from shared.unit_of_work import UnitOfWork


class ProgramCreationService:
    def _ensure_program_topic_material_target(self, db: Session, *, program_id: int, block_id: int, topic_id: int | None, task_id: int | None):
        if (topic_id is None) == (task_id is None):
            raise PermissionDenied("Specify exactly one topic or task")

        if topic_id is not None:
            topic = (
                db.query(ProgramTopic)
                .filter(ProgramTopic.id == topic_id, ProgramTopic.block_id == block_id)
                .first()
            )
            if not topic or topic.block.program_id != program_id:
                raise PermissionDenied("Topic does not belong to program")
            return topic, None

        task = (
            db.query(ProgramTask)
            .filter(ProgramTask.id == task_id, ProgramTask.block_id == block_id)
            .first()
        )
        if not task or task.block.program_id != program_id:
            raise PermissionDenied("Task does not belong to program")
        return None, task

    async def add_topic_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, topic_id: int, file):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block or block.program_id != program_id:
                raise PermissionDenied("Block not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc

            topic = db.query(ProgramTopic).filter(ProgramTopic.id == topic_id, ProgramTopic.block_id == block_id).first()
            if not topic:
                raise PermissionDenied("Topic not found")

            file_key = await file_service.upload_material(file)
            material = ProgramMaterial(topic_id=topic.id, file_url=file_key, file_name=file.filename or "material", content_type=file.content_type)
            db.add(material)
            db.flush()
            db.refresh(material)
            return material

    async def add_task_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, task_id: int, file):
        with UnitOfWork(db):
            block = program_repository.get_block_by_id(db, block_id)
            if not block or block.program_id != program_id:
                raise PermissionDenied("Block not found")
            try:
                ProgramPolicy.require_edit_program(ctx, block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc

            task = db.query(ProgramTask).filter(ProgramTask.id == task_id, ProgramTask.block_id == block_id).first()
            if not task:
                raise PermissionDenied("Task not found")

            file_key = await file_service.upload_material(file)
            material = ProgramMaterial(task_id=task.id, file_url=file_key, file_name=file.filename or "material", content_type=file.content_type)
            db.add(material)
            db.flush()
            db.refresh(material)
            return material

    def delete_material(self, db: Session, *, ctx: AccessContext, program_id: int, material_id: int):
        with UnitOfWork(db):
            material = db.query(ProgramMaterial).filter(ProgramMaterial.id == material_id).first()
            if not material:
                raise PermissionDenied("Material not found")

            if material.topic_id is not None:
                topic = db.query(ProgramTopic).filter(ProgramTopic.id == material.topic_id).first()
                if not topic or topic.block.program_id != program_id:
                    raise PermissionDenied("Material does not belong to program")
            elif material.task_id is not None:
                task = db.query(ProgramTask).filter(ProgramTask.id == material.task_id).first()
                if not task or task.block.program_id != program_id:
                    raise PermissionDenied("Material does not belong to program")

            try:
                ProgramPolicy.require_edit_program(ctx, task.block.program if material.task_id else topic.block.program)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to edit program") from exc

            file_service.delete_file(material.file_url, BUCKET_NAMES["documents"])
            db.delete(material)
            db.flush()

    def _assign_task_to_group_enrollments(self, db: Session, *, program_id: int, task_id: int):
        group_enrollments = (
            db.query(GroupEnrollment)
            .join(Group, Group.id == GroupEnrollment.group_id)
            .filter(Group.program_id == program_id)
            .all()
        )

        for enrollment in group_enrollments:
            exists = (
                db.query(GroupStudentTask)
                .filter(
                    GroupStudentTask.enrollment_id == enrollment.id,
                    GroupStudentTask.program_task_id == task_id,
                )
                .first()
            )
            if exists:
                continue
            db.add(GroupStudentTask(enrollment_id=enrollment.id, program_task_id=task_id, status="assigned"))

        db.flush()

    def reconcile_program_group_tasks(self, db: Session, *, program_id: int):
        program = program_repository.get_by_id(db, program_id)
        if not program:
            raise PermissionDenied("Program not found")

        tasks = (
            db.query(ProgramTask)
            .join(ProgramTask.block)
            .filter(ProgramTask.block.has(program_id=program_id))
            .all()
        )
        for task in tasks:
            self._assign_task_to_group_enrollments(db, program_id=program_id, task_id=task.id)

        return len(tasks)

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

            task = program_repository.create_task(
                db,
                block_id=block.id,
                topic_id=topic_id,
                title=title,
                description=description,
                max_score=max_score,
                is_manual=is_manual,
            )
            self._assign_task_to_group_enrollments(db, program_id=program.id, task_id=task.id)
            return task

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
