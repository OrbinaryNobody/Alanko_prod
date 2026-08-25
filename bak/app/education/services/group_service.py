from datetime import date, time

from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.policies.group_policy import GroupPolicy
from education.repositories.group_repository import group_repository
from education.services.group_management_service import group_management_service
from models.domains.auth import Role, User
from models.domains.education import GroupSchedule


class GroupService:
    def ensure_group_access(self, db: Session, *, ctx: AccessContext, group_id: int):
        group = group_repository.get_by_id(db, group_id)
        if not group:
            raise PermissionDenied("Group not found")
        try:
            GroupPolicy.require_view_group(ctx, group)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to this group") from exc
        return group

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return group_management_service.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def get_groups_for_user(self, db: Session, *, ctx: AccessContext):
        return group_repository.list_for_user(db, user_id=ctx.user_id, is_admin=ctx.is_admin)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return group_management_service.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def add_teacher_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int):
        return group_management_service.add_teacher_member(db, ctx=ctx, group_id=group_id, user_id=user_id)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return group_management_service.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def get_group_students(self, db: Session, *, ctx: AccessContext, group_id: int):
        from education.dtos.student_dto import GroupStudentPayload

        self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        enrollments = group_repository.list_enrollments(db, group_id=group_id)
        return [
            GroupStudentPayload(
                id=enrollment.id,
                student_id=enrollment.student_id,
                status=enrollment.status,
                current_block_id=enrollment.current_block_id,
                completion_percent=enrollment.completion_percent,
            ).to_dict()
            for enrollment in enrollments
        ]

    def list_schedules(self, db: Session, *, ctx: AccessContext, group_id: int):
        self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        return group_repository.list_schedules(db, group_id=group_id)

    def create_schedule(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        group_id: int,
        teacher_id: int,
        weekday: int,
        start_time: time,
        end_time: time,
        valid_from: date,
        valid_until: date | None,
    ):
        group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        teacher = db.query(User).join(User.roles).join(Role).filter(
            User.id == teacher_id,
            Role.name == "teacher",
        ).first()
        if not teacher:
            raise PermissionDenied("Teacher not found")

        schedules = group_repository.list_schedules(db, group_id=group_id)
        for schedule in schedules:
            if schedule.status != "ACTIVE" or schedule.weekday != weekday:
                continue
            periods_overlap = (
                schedule.valid_from <= (valid_until or date.max)
                and (schedule.valid_until is None or schedule.valid_until >= valid_from)
            )
            times_overlap = schedule.start_time < end_time and schedule.end_time > start_time
            if periods_overlap and times_overlap:
                raise PermissionDenied("Schedule overlaps with an existing group lesson")

        return group_repository.create_schedule(db, GroupSchedule(
            group_id=group.id,
            teacher_id=teacher_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            valid_from=valid_from,
            valid_until=valid_until,
        ))

    def delete_schedule(self, db: Session, *, ctx: AccessContext, schedule_id: int):
        schedule = group_repository.get_schedule(db, schedule_id=schedule_id)
        if not schedule:
            raise PermissionDenied("Schedule not found")
        self.ensure_group_access(db, ctx=ctx, group_id=schedule.group_id)
        group_repository.delete_schedule(db, schedule)

    def list_calendar_schedules(self, db: Session, *, date_from: date, date_to: date):
        return group_repository.list_active_schedules(db, date_from=date_from, date_to=date_to)


group_service = GroupService()
