from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied, ProgramNotFound
from education.repositories.program_repository import program_repository
from education.services.program_read_service import program_read_service
from models.domains.education import Program, ProgramBlock, ProgramChangeProposal, ProgramMaterial, ProgramTask, ProgramTopic
from shared.unit_of_work import UnitOfWork


class ProgramChangeService:
    def _snapshot(self, db: Session, program_id: int) -> dict:
        program = db.query(Program).options(
            joinedload(Program.blocks).joinedload(ProgramBlock.topics).joinedload(ProgramTopic.tasks),
            joinedload(Program.blocks).joinedload(ProgramBlock.tasks),
        ).filter(Program.id == program_id).first()
        if not program:
            raise ProgramNotFound("Program not found")
        return {
            "program_id": program.id,
            "blocks": [
                {
                    "id": block.id,
                    "title": block.title,
                    "description": block.description,
                    "order": block.order,
                    "topics": self._topic_snapshot(block),
                }
                for block in sorted(program.blocks, key=lambda item: (item.order, item.id))
            ],
        }

    def _task_snapshot(self, task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "max_score": task.max_score,
            "order": task.order,
            "is_manual": task.is_manual,
            "materials": [{
                "id": material.id,
                "file_name": material.file_name,
                "content_type": material.content_type,
                "file_url": material.file_url,
            } for material in sorted(task.materials, key=lambda item: (item.id or 0))],
        }

    def _topic_snapshot(self, block) -> list[dict]:
        topics = [
            {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "order": topic.order,
                "materials": [{
                    "id": material.id,
                    "file_name": material.file_name,
                    "content_type": material.content_type,
                    "file_url": material.file_url,
                } for material in sorted(topic.materials, key=lambda item: (item.id or 0))],
                "tasks": [self._task_snapshot(task) for task in sorted(topic.tasks, key=lambda item: (item.order, item.id))],
            }
            for topic in sorted(block.topics, key=lambda item: (item.order, item.id))
        ]
        legacy_tasks = [task for task in block.tasks if task.topic_id is None]
        if legacy_tasks:
            topics.append({
                "id": None,
                "title": "Без темы",
                "description": None,
                "order": max((topic["order"] for topic in topics), default=-1) + 1,
                "tasks": [self._task_snapshot(task) for task in sorted(legacy_tasks, key=lambda item: (item.order, item.id))],
            })
        return topics

    def create_proposal(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        program_id: int | None,
        blocks: list[dict],
        comment: str | None,
        title: str | None = None,
        description: str | None = None,
    ):
        with UnitOfWork(db):
            if program_id is not None:
                program_read_service.ensure_program_access(db, ctx=ctx, program_id=program_id)

            if program_id is not None:
                active = db.query(ProgramChangeProposal).filter(
                    ProgramChangeProposal.program_id == program_id,
                    ProgramChangeProposal.author_id == ctx.user_id,
                    ProgramChangeProposal.status == "PENDING",
                ).first()
                if active:
                    raise PermissionDenied("A pending proposal already exists")
                base = self._snapshot(db, program_id)
            else:
                base = {"program_id": None, "title": title or "", "description": description, "blocks": []}

            proposed = {
                "program_id": program_id,
                "title": title or "",
                "description": description,
                "blocks": blocks,
            }
            proposal = ProgramChangeProposal(
                program_id=program_id,
                proposal_type="CREATE" if program_id is None else "UPDATE",
                author_id=ctx.user_id,
                base_snapshot=base,
                proposed_snapshot=proposed,
                author_comment=comment,
            )
            db.add(proposal)
            db.flush()
            db.refresh(proposal)
            return proposal

    def list_proposals(self, db: Session, *, ctx: AccessContext, own_only: bool = False):
        query = db.query(ProgramChangeProposal).order_by(ProgramChangeProposal.created_at.desc())
        if own_only:
            return query.filter(ProgramChangeProposal.author_id == ctx.user_id).all()
        if not ctx.is_admin:
            raise PermissionDenied("Only administrators can review proposals")
        return query.all()

    def get_proposal(self, db: Session, *, ctx: AccessContext, proposal_id: int):
        proposal = db.query(ProgramChangeProposal).filter(ProgramChangeProposal.id == proposal_id).first()
        if not proposal:
            raise ProgramNotFound("Proposal not found")
        if not ctx.is_admin and proposal.author_id != ctx.user_id:
            raise PermissionDenied("Access denied to proposal")
        return proposal

    def _apply_snapshot(self, db: Session, program_id: int, snapshot: dict):
        program = db.query(Program).options(
            joinedload(Program.blocks).joinedload(ProgramBlock.topics).joinedload(ProgramTopic.tasks),
            joinedload(Program.blocks).joinedload(ProgramBlock.tasks),
        ).filter(Program.id == program_id).first()
        current_blocks = {block.id: block for block in program.blocks}
        incoming_ids = {item["id"] for item in snapshot["blocks"] if item.get("id") is not None}
        for block_id, block in current_blocks.items():
            if block_id not in incoming_ids:
                db.delete(block)
        for block_data in snapshot["blocks"]:
            block = current_blocks.get(block_data.get("id"))
            if block is None:
                block = ProgramBlock(program_id=program_id, status="draft")
                db.add(block)
            block.title = block_data["title"]
            block.description = block_data.get("description")
            block.order = block_data.get("order", 0)
            current_topics = {topic.id: topic for topic in block.topics}
            topic_data_list = block_data.get("topics")
            if topic_data_list is None:
                topic_data_list = [{
                    "id": None,
                    "title": "Без темы",
                    "description": None,
                    "order": 0,
                    "tasks": block_data.get("tasks", []),
                }]
            incoming_topic_ids = {item["id"] for item in topic_data_list if item.get("id") is not None}
            for topic_id, topic in current_topics.items():
                if topic_id not in incoming_topic_ids:
                    db.delete(topic)
            for topic_data in topic_data_list:
                topic = current_topics.get(topic_data.get("id"))
                if topic is None:
                    topic = ProgramTopic(block=block, status="draft")
                    db.add(topic)
                topic.title = topic_data["title"]
                topic.description = topic_data.get("description")
                topic.order = topic_data.get("order", 0)
                current_tasks = {task.id: task for task in topic.tasks}
                current_topic_materials = {material.id: material for material in topic.materials}
                incoming_topic_material_ids = {item["id"] for item in topic_data.get("materials", []) if item.get("id") is not None}
                for material_id, material in current_topic_materials.items():
                    if material_id not in incoming_topic_material_ids:
                        db.delete(material)
                for material_data in topic_data.get("materials", []):
                    if material_data.get("id") is not None:
                        continue
                    material = ProgramMaterial(topic_id=topic.id, file_url=material_data.get("file_url"), file_name=material_data.get("file_name", "material"), content_type=material_data.get("content_type"))
                    db.add(material)

                if topic_data.get("id") is None:
                    current_tasks.update({task.id: task for task in block.tasks if task.topic_id is None})
                incoming_task_ids = {item["id"] for item in topic_data.get("tasks", []) if item.get("id") is not None}
                for task_id, task in current_tasks.items():
                    if task_id not in incoming_task_ids:
                        db.delete(task)
                for task_data in topic_data.get("tasks", []):
                    task = current_tasks.get(task_data.get("id"))
                    if task is None:
                        task = ProgramTask(block=block, topic=topic)
                        db.add(task)
                    task.title = task_data["title"]
                    task.description = task_data.get("description")
                    task.max_score = task_data.get("max_score", 100)
                    task.order = task_data.get("order", 0)
                    task.is_manual = task_data.get("is_manual", False)

                    current_task_materials = {material.id: material for material in task.materials}
                    incoming_task_material_ids = {item["id"] for item in task_data.get("materials", []) if item.get("id") is not None}
                    for material_id, material in current_task_materials.items():
                        if material_id not in incoming_task_material_ids:
                            db.delete(material)
                    for material_data in task_data.get("materials", []):
                        if material_data.get("id") is not None:
                            continue
                        material = ProgramMaterial(task_id=task.id, file_url=material_data.get("file_url"), file_name=material_data.get("file_name", "material"), content_type=material_data.get("content_type"))
                        db.add(material)

    def decide(self, db: Session, *, ctx: AccessContext, proposal_id: int, approved: bool, comment: str | None):
        if not ctx.is_admin:
            raise PermissionDenied("Only administrators can decide proposals")
        with UnitOfWork(db):
            proposal = self.get_proposal(db, ctx=ctx, proposal_id=proposal_id)
            if proposal.status != "PENDING":
                raise PermissionDenied("Only pending proposals can be decided")
            if approved:
                if proposal.program_id is None:
                    proposed = proposal.proposed_snapshot or {}
                    program = Program(
                        title=(proposed.get("title") or "Новая программа").strip() or "Новая программа",
                        description=proposed.get("description"),
                        created_by=proposal.author_id,
                        status="draft",
                    )
                    db.add(program)
                    db.flush()
                    db.refresh(program)
                    proposal.program_id = program.id
                    self._apply_snapshot(db, program.id, proposed)
                else:
                    current = self._snapshot(db, proposal.program_id)
                    if current != proposal.base_snapshot:
                        raise PermissionDenied("Program changed after proposal was submitted")
                    self._apply_snapshot(db, proposal.program_id, proposal.proposed_snapshot)
                proposal.status = "APPROVED"
            else:
                proposal.status = "REJECTED"
            proposal.reviewer_comment = comment
            proposal.reviewed_by = ctx.user_id
            proposal.reviewed_at = datetime.now(timezone.utc)
            db.flush()
            db.refresh(proposal)
            return proposal


program_change_service = ProgramChangeService()