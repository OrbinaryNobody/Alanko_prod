from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Group, GroupMember, GroupRole, Program, ProgramBlock, ProgramTask, User


class ProgramService:
    def ensure_program_access(self, db: Session, *, program_id: int, user_id: int, is_admin: bool = False):
        program = db.query(Program).filter(Program.id == program_id).first()
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        if not is_admin and program.created_by != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this program")
        return program

    def create_program(self, db: Session, *, title: str, description: str | None, created_by: int):
        program = Program(title=title, description=description, created_by=created_by, status="draft")
        db.add(program)
        db.commit()
        db.refresh(program)
        return program

    def get_programs_for_user(self, db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return (
            db.query(Program)
            .filter((Program.created_by == user_id) | (Program.status == "draft"))
            .order_by(Program.created_at.desc())
            .all()
        )

    def create_block(self, db: Session, *, program_id: int, title: str, description: str | None, order: int, user_id: int, is_admin: bool = False):
        program = self.ensure_program_access(db, program_id=program_id, user_id=user_id, is_admin=is_admin)

        block = ProgramBlock(program_id=program.id, title=title, description=description, order=order)
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    def create_task(self, db: Session, *, block_id: int, title: str, description: str | None, max_score: int, is_manual: bool, user_id: int, is_admin: bool = False):
        block = db.query(ProgramBlock).filter(ProgramBlock.id == block_id).first()
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")

        self.ensure_program_access(db, program_id=block.program_id, user_id=user_id, is_admin=is_admin)

        task = ProgramTask(
            block_id=block.id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_program_blocks(self, db: Session, *, program_id: int):
        return (
            db.query(ProgramBlock)
            .filter(ProgramBlock.program_id == program_id)
            .order_by(ProgramBlock.order.asc())
            .all()
        )


program_service = ProgramService()
