from sqlalchemy.orm import Session

from core.access import AccessContext

# Public contract for the education context. Other contexts should use this facade
# instead of importing education services or repositories directly.
from education.services.group_service import group_service as education_group_service
from education.services.program_service import program_service as education_program_service
from education.services.student_service import student_service as education_student_service
from education.services.task_service import task_service as education_task_service
from education.services.program_change_service import program_change_service


class EducationFacade:
    def create_program(self, db: Session, *, ctx: AccessContext, title: str, description: str | None):
        return education_program_service.create_program(db, ctx=ctx, title=title, description=description)

    def create_block(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None, order: int):
        return education_program_service.create_block(db, ctx=ctx, program_id=program_id, title=title, description=description, order=order)

    def create_topic(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        return education_program_service.create_topic(db, ctx=ctx, block_id=block_id, title=title, description=description, order=order)

    def create_task(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        title: str,
        description: str | None,
        difficulty: int,
        max_score: int,
    ):
        return education_task_service.create_task(
            db,
            ctx=ctx,
            title=title,
            description=description,
            difficulty=difficulty,
            max_score=max_score,
        )

    def create_task_for_block(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        block_id: int,
        topic_id: int | None,
        title: str,
        description: str | None,
        max_score: int,
        is_manual: bool,
    ):
        return education_program_service.create_task(
            db,
            ctx=ctx,
            block_id=block_id,
            topic_id=topic_id,
            title=title,
            description=description,
            max_score=max_score,
            is_manual=is_manual,
        )

    def update_block(self, db: Session, *, ctx: AccessContext, block_id: int, title: str, description: str | None, order: int):
        return education_program_service.update_block(db, ctx=ctx, block_id=block_id, title=title, description=description, order=order)

    def update_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, title: str, description: str | None, order: int):
        return education_program_service.update_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id, title=title, description=description, order=order)

    def update_program_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int, title: str, description: str | None, max_score: int, is_manual: bool, order: int):
        return education_program_service.update_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id, title=title, description=description, max_score=max_score, is_manual=is_manual, order=order)

    def delete_block(self, db: Session, *, ctx: AccessContext, block_id: int):
        return education_program_service.delete_block(db, ctx=ctx, block_id=block_id)

    def delete_topic(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int):
        return education_program_service.delete_topic(db, ctx=ctx, block_id=block_id, topic_id=topic_id)

    def delete_program_task(self, db: Session, *, ctx: AccessContext, block_id: int, topic_id: int, task_id: int):
        return education_program_service.delete_task(db, ctx=ctx, block_id=block_id, topic_id=topic_id, task_id=task_id)

    async def add_topic_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, topic_id: int, file):
        return await education_program_service.add_topic_material(db, ctx=ctx, program_id=program_id, block_id=block_id, topic_id=topic_id, file=file)

    async def add_task_material(self, db: Session, *, ctx: AccessContext, program_id: int, block_id: int, task_id: int, file):
        return await education_program_service.add_task_material(db, ctx=ctx, program_id=program_id, block_id=block_id, task_id=task_id, file=file)

    def delete_program_material(self, db: Session, *, ctx: AccessContext, program_id: int, material_id: int):
        return education_program_service.delete_material(db, ctx=ctx, program_id=program_id, material_id=material_id)

    def get_programs_for_user(self, db: Session, *, ctx: AccessContext):
        return education_program_service.get_programs_for_user(db, ctx=ctx)

    def get_program_by_id(self, db: Session, *, ctx: AccessContext, program_id: int):
        return education_program_service.get_program_by_id(db, ctx=ctx, program_id=program_id)

    def update_program(self, db: Session, *, ctx: AccessContext, program_id: int, title: str, description: str | None):
        return education_program_service.update_program(db, ctx=ctx, program_id=program_id, title=title, description=description)

    def create_program_change_proposal(
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
        return program_change_service.create_proposal(
            db,
            ctx=ctx,
            program_id=program_id,
            blocks=blocks,
            comment=comment,
            title=title,
            description=description,
        )

    def list_my_program_change_proposals(self, db: Session, *, ctx: AccessContext):
        return program_change_service.list_proposals(db, ctx=ctx, own_only=True)

    def list_program_change_proposals(self, db: Session, *, ctx: AccessContext):
        return program_change_service.list_proposals(db, ctx=ctx)

    def get_program_change_proposal(self, db: Session, *, ctx: AccessContext, proposal_id: int):
        return program_change_service.get_proposal(db, ctx=ctx, proposal_id=proposal_id)

    def approve_program_change_proposal(self, db: Session, *, ctx: AccessContext, proposal_id: int, comment: str | None):
        return program_change_service.decide(db, ctx=ctx, proposal_id=proposal_id, approved=True, comment=comment)

    def reject_program_change_proposal(self, db: Session, *, ctx: AccessContext, proposal_id: int, comment: str | None):
        return program_change_service.decide(db, ctx=ctx, proposal_id=proposal_id, approved=False, comment=comment)

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return education_group_service.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def update_group(self, db: Session, *, ctx: AccessContext, group_id: int, title: str, description: str | None, leaderboard_enabled: bool):
        return education_group_service.update_group(db, ctx=ctx, group_id=group_id, title=title, description=description, leaderboard_enabled=leaderboard_enabled)

    def delete_group(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.delete_group(db, ctx=ctx, group_id=group_id)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return education_group_service.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def add_teacher_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int):
        return education_group_service.add_teacher_member(db, ctx=ctx, group_id=group_id, user_id=user_id)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return education_group_service.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def delete_enrollment(self, db: Session, *, ctx: AccessContext, group_id: int, enrollment_id: int):
        return education_group_service.delete_enrollment(db, ctx=ctx, group_id=group_id, enrollment_id=enrollment_id)

    def has_active_registration(self, db: Session, *, ctx: AccessContext, course_id: int) -> bool:
        from models.domains.payments import CourseEnrollment

        return (
            db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == ctx.user_id)
            .filter(CourseEnrollment.course_id == course_id)
            .filter(CourseEnrollment.status == "ACTIVE")
            .first()
            is not None
        )

    def register_user_for_course(self, db: Session, *, ctx: AccessContext, course_id: int, payment_id: int):
        from core.exceptions import NotFoundError
        from models.domains.payments import CourseEnrollment, Payment

        payment = db.query(Payment).filter(Payment.id == payment_id).one_or_none()
        if payment is None:
            raise NotFoundError("PAYMENT_NOT_FOUND")

        enrollment = (
            db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == ctx.user_id)
            .filter(CourseEnrollment.course_id == course_id)
            .order_by(CourseEnrollment.id.desc())
            .first()
        )
        if enrollment is not None:
            if enrollment.status == "ACTIVE":
                return enrollment
            enrollment.status = "ACTIVE"
            enrollment.payment_id = payment.id
            db.flush()
            return enrollment

        enrollment = CourseEnrollment(
            user_id=ctx.user_id,
            course_id=course_id,
            payment_id=payment.id,
            status="ACTIVE",
        )
        db.add(enrollment)
        db.flush()
        return enrollment

    def get_groups_for_user(self, db: Session, *, ctx: AccessContext):
        return education_group_service.get_groups_for_user(db, ctx=ctx)

    def get_group(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.ensure_group_access(db, ctx=ctx, group_id=group_id)

    def get_group_students(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.get_group_students(db, ctx=ctx, group_id=group_id)

    def get_group_journal(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.get_group_journal(db, ctx=ctx, group_id=group_id)

    def grade_group_task(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, grade: int, feedback: str | None):
        return education_group_service.grade_group_task(db, ctx=ctx, group_id=group_id, student_task_id=student_task_id, grade=grade, feedback=feedback)

    def upload_group_task_video(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, video_url: str):
        return education_group_service.upload_group_task_video(db, ctx=ctx, group_id=group_id, student_task_id=student_task_id, video_url=video_url)

    def delete_group_task_video(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, media_id: int):
        return education_group_service.delete_group_task_video(db, ctx=ctx, group_id=group_id, student_task_id=student_task_id, media_id=media_id)

    def add_group_material(self, db: Session, *, ctx: AccessContext, group_id: int, topic_id: int | None, task_id: int | None, file_url: str, file_name: str, content_type: str | None):
        return education_group_service.add_group_material(db, ctx=ctx, group_id=group_id, topic_id=topic_id, task_id=task_id, file_url=file_url, file_name=file_name, content_type=content_type)

    def delete_group_material(self, db: Session, *, ctx: AccessContext, group_id: int, material_id: int):
        return education_group_service.delete_group_material(db, ctx=ctx, group_id=group_id, material_id=material_id)

    def list_group_schedules(self, db: Session, *, ctx: AccessContext, group_id: int):
        return education_group_service.list_schedules(db, ctx=ctx, group_id=group_id)

    def create_group_schedule(self, db: Session, *, ctx: AccessContext, group_id: int, **data):
        return education_group_service.create_schedule(db, ctx=ctx, group_id=group_id, **data)

    def delete_group_schedule(self, db: Session, *, ctx: AccessContext, schedule_id: int):
        return education_group_service.delete_schedule(db, ctx=ctx, schedule_id=schedule_id)

    def list_calendar_schedules(self, db: Session, *, date_from, date_to):
        return education_group_service.list_calendar_schedules(db, date_from=date_from, date_to=date_to)

    def upload_student_task_video(self, db: Session, *, ctx: AccessContext, student_task_id: int, uploaded_by: int, video_url: str):
        return education_student_service.upload_student_task_video(
            db,
            ctx=ctx,
            student_task_id=student_task_id,
            uploaded_by=uploaded_by,
            video_url=video_url,
        )

    def ensure_student_task_video_access(self, db: Session, *, ctx: AccessContext, student_task_id: int):
        return education_student_service.ensure_student_task_video_access(
            db,
            ctx=ctx,
            student_task_id=student_task_id,
        )

    def get_student_by_id(self, db: Session, *, student_id: int):
        return education_student_service.get_student_by_id(db, student_id=student_id)

    def update_student_task(self, db: Session, *, ctx: AccessContext, student_task_id: int, student_task_data):
        return education_student_service.update_student_task(
            db,
            ctx=ctx,
            student_task_id=student_task_id,
            student_task_data=student_task_data,
        )

    def get_students_payload(self, db: Session, *, ctx: AccessContext, **filters):
        return education_student_service.get_students_payload(db, **filters)

    def get_students_tasks_payload(self, db: Session, *, ctx: AccessContext):
        return education_student_service.get_students_tasks_payload(db)

    def get_tasks(self, db: Session, *, ctx: AccessContext):
        return education_task_service.get_tasks(db)

    def get_task(self, db: Session, *, ctx: AccessContext, task_id: int):
        return education_task_service.get_task(db, task_id=task_id)

    def update_task(self, db: Session, *, ctx: AccessContext, task_id: int, task_data):
        return education_task_service.update_task(db, task_id=task_id, task_data=task_data)


education_facade = EducationFacade()
