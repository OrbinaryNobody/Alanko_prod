from sqlalchemy.orm import Session

from admin.services.admin_service import admin_service
from core.access import AccessContext


class AdminFacade:
    def add_user_by_admin(self, db: Session, *, data):
        return admin_service.add_user_by_admin(db, data=data)

    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        return admin_service.create_program(db, ctx=ctx, title=title, description=description)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        return admin_service.create_block(db, ctx=ctx, program_id=program_id, title=title, description=description, order=order)

    def create_task(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, max_score: int, is_manual: bool):
        return admin_service.create_task(db, ctx=ctx, block_id=block_id, title=title, description=description, max_score=max_score, is_manual=is_manual)

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return admin_service.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return admin_service.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return admin_service.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def get_dashboard_payload(self, db: Session, *, ctx: AccessContext):
        return admin_service.get_dashboard_payload(db, ctx=ctx)

    def get_student_tasks_payload(self, db: Session, *, ctx: AccessContext):
        return admin_service.get_student_tasks_payload(db, ctx=ctx)


admin_facade = AdminFacade()
