from sqlalchemy.orm import Session

from models.domains.education import Program, ProgramBlock, ProgramTask


class ProgramRepository:
    def get_by_id(self, db: Session, program_id: int) -> Program | None:
        return db.query(Program).filter(Program.id == program_id).first()

    def list_for_user(self, db: Session, *, user_id: int, is_admin: bool = False) -> list[Program]:
        if is_admin:
            return db.query(Program).order_by(Program.created_at.desc()).all()

        return (
            db.query(Program)
            .filter((Program.created_by == user_id) | (Program.status == "draft"))
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

    def create_task(self, db: Session, *, block_id: int, title: str, description: str | None, max_score: int, is_manual: bool) -> ProgramTask:
        task = ProgramTask(
            block_id=block_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )
        db.add(task)
        db.flush()
        db.refresh(task)
        return task

    def list_blocks(self, db: Session, *, program_id: int) -> list[ProgramBlock]:
        return (
            db.query(ProgramBlock)
            .filter(ProgramBlock.program_id == program_id)
            .order_by(ProgramBlock.order.asc())
            .all()
        )


program_repository = ProgramRepository()
