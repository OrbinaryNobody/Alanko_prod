from sqlalchemy.orm import Session

from accounts.facade import accounts_facade
from core.access import AccessContext
from core.exceptions import ConflictError
from education.facade import education_facade
from profile.facade import profile_facade


class AdminService:
    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        return education_facade.create_program(db, ctx=ctx, title=title, description=description)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        return education_facade.create_block(db, ctx=ctx, program_id=program_id, title=title, description=description, order=order)

    def create_task(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, max_score: int, is_manual: bool):
        return education_facade.create_task_for_block(
            db,
            ctx=ctx,
            block_id=block_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return education_facade.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return education_facade.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return education_facade.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def add_user_by_admin(self, db: Session, *, data):
        try:
            return accounts_facade.add_user_by_admin(db, data=data)
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

    def get_dashboard_payload(self, db: Session, *, ctx: AccessContext):
        return profile_facade.get_dashboard_payload(db, ctx=ctx)

    def get_student_tasks_payload(self, db: Session, *, ctx: AccessContext):
        return profile_facade.get_student_tasks_payload(db, ctx=ctx)


admin_service = AdminService()
