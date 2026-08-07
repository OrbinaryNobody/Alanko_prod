from sqlalchemy.orm import Session

from core.access import AccessContext

# Public contract for the education context. Other contexts should use this facade
# instead of importing education services or repositories directly.
from education.services.group_service import group_service as education_group_service
from education.services.program_service import program_service as education_program_service
from education.services.student_service import student_service as education_student_service
from education.services.task_service import task_service as education_task_service


class EducationFacade:
    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        return education_program_service.create_program(db, ctx=ctx, title=title, description=description)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        return education_program_service.create_block(db, ctx=ctx, program_id=program_id, title=title, description=description, order=order)

    def create_task(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        title: str,
        description: str | None,
        category_id: int,
        difficulty: int,
        max_score: int,
    ):
        return education_task_service.create_task(
            db,
            ctx=ctx,
            title=title,
            description=description,
            category_id=category_id,
            difficulty=difficulty,
            max_score=max_score,
        )

    def create_task_for_block(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        block_id: int,
        title: str,
        description: str | None,
        max_score: int,
        is_manual: bool,
    ):
        return education_program_service.create_task(
            db,
            ctx=ctx,
            block_id=block_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )

    def get_programs_for_user(self, db: Session, *, ctx: AccessContext):
        return education_program_service.get_programs_for_user(db, ctx=ctx)

    def get_program_by_id(self, db: Session, *, ctx: AccessContext, program_id: int):
        return education_program_service.get_program_by_id(db, ctx=ctx, program_id=program_id)

    def update_program(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None):
        return education_program_service.update_program(db, ctx=ctx, program_id=program_id, title=title, description=description)

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return education_group_service.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return education_group_service.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return education_group_service.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def get_groups_for_user(self, db: Session, *, ctx: AccessContext):
        return education_group_service.get_groups_for_user(db, ctx=ctx)

    def get_group_students(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.get_group_students(db, ctx=ctx, group_id=group_id)

    def upload_student_task_video(self, db: Session, *, student_task_id: int, uploaded_by: int, video_url: str):
        return education_student_service.upload_student_task_video(
            db,
            student_task_id=student_task_id,
            uploaded_by=uploaded_by,
            video_url=video_url,
        )

    def get_student_by_id(self, db: Session, *, student_id: int):
        return education_student_service.get_student_by_id(db, student_id=student_id)

    def update_student_task(self, db: Session, *, student_task_id: int, student_task_data):
        return education_student_service.update_student_task(
            db,
            student_task_id=student_task_id,
            student_task_data=student_task_data,
        )

    def get_students_payload(self, db: Session, *, ctx: AccessContext):
        return education_student_service.get_students_payload(db)

    def get_students_tasks_payload(self, db: Session, *, ctx: AccessContext):
        return education_student_service.get_students_tasks_payload(db)

    def get_tasks(self, db: Session, *, ctx: AccessContext):
        return education_task_service.get_tasks(db)

    def get_task(self, db: Session, *, ctx: AccessContext, task_id: int):
        return education_task_service.get_task(db, task_id=task_id)

    def update_task(self, db: Session, *, ctx: AccessContext, task_id: int, task_data):
        return education_task_service.update_task(db, task_id=task_id, task_data=task_data)


education_facade = EducationFacade()
