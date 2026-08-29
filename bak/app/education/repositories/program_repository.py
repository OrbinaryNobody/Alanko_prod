from sqlalchemy.orm import Session

from models.domains.education import Group, GroupMember, Program, ProgramBlock, ProgramTask, ProgramTopic


class ProgramRepository:
    def get_by_id(self, db: Session, program_id: int) -> Program | None:
        return db.query(Program).filter(Program.id == program_id).first()

    def has_teacher_access(self, db: Session, *, user_id: int, program_id: int) -> bool:
        return (
            db.query(GroupMember.user_id)
            .join(Group, Group.id == GroupMember.group_id)
            .filter(
                GroupMember.user_id == user_id,
                GroupMember.role == "teacher",
                Group.program_id == program_id,
            )
            .first()
            is not None
        )

    def list_for_user(self, db: Session, *, user_id: int, is_admin: bool = False) -> list[Program]:
        if is_admin:
            return db.query(Program).order_by(Program.created_at.desc()).all()

        assigned_program_ids = (
            db.query(Group.program_id)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .filter(GroupMember.user_id == user_id, GroupMember.role == "teacher")
            .filter(Group.program_id.isnot(None))
            .subquery()
        )

        return (
            db.query(Program)
            .filter(Program.id.in_(assigned_program_ids))
            .order_by(Program.created_at.desc())
            .all()
        )

    def create(self, db: Session, *, title: str, description: str | None, created_by: int) -> Program:
        program = Program(title=title, description=description, created_by=created_by, status="draft")
        db.add(program)
        db.flush()
        db.refresh(program)
        return program

    def update(self, db: Session, program: Program) -> Program:
        db.flush()
        db.refresh(program)
        return program

    def create_block(self, db: Session, *, program_id: int, title: str, description: str | None, order: int) -> ProgramBlock:
        block = ProgramBlock(program_id=program_id, title=title, description=description, order=order)
        db.add(block)
        db.flush()
        db.refresh(block)
        return block

    def get_block_by_id(self, db: Session, block_id: int) -> ProgramBlock | None:
        return db.query(ProgramBlock).filter(ProgramBlock.id == block_id).first()

    def get_topic_by_id(self, db: Session, topic_id: int) -> ProgramTopic | None:
        return db.query(ProgramTopic).filter(ProgramTopic.id == topic_id).first()

    def get_task_by_id(self, db: Session, task_id: int) -> ProgramTask | None:
        return db.query(ProgramTask).filter(ProgramTask.id == task_id).first()

    def create_topic(self, db: Session, *, block_id: int, title: str, description: str | None, order: int) -> ProgramTopic:
        topic = ProgramTopic(block_id=block_id, title=title, description=description, order=order)
        db.add(topic)
        db.flush()
        db.refresh(topic)
        return topic

    def create_task(self, db: Session, *, block_id: int, topic_id: int | None, title: str, description: str | None, max_score: int, is_manual: bool) -> ProgramTask:
        task = ProgramTask(
            block_id=block_id,
            topic_id=topic_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )
        db.add(task)
        db.flush()
        db.refresh(task)
        return task

    def delete_block(self, db: Session, block: ProgramBlock) -> None:
        db.delete(block)
        db.flush()

    def delete_topic(self, db: Session, topic: ProgramTopic) -> None:
        db.delete(topic)
        db.flush()

    def delete_task(self, db: Session, task: ProgramTask) -> None:
        db.delete(task)
        db.flush()

    def list_blocks(self, db: Session, *, program_id: int) -> list[ProgramBlock]:
        return (
            db.query(ProgramBlock)
            .filter(ProgramBlock.program_id == program_id)
            .order_by(ProgramBlock.order.asc())
            .all()
        )


program_repository = ProgramRepository()
