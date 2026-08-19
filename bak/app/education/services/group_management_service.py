from sqlalchemy.orm import Session

from core.access import AccessContext
from core.events import event_bus
from education.exceptions.domain_exceptions import PermissionDenied
from education.events import GroupCreatedEvent, StudentEnrolledEvent
from education.policies.group_policy import GroupPolicy
from education.repositories.group_repository import group_repository
from models.domains.auth import GroupRole, User
from models.domains.education import Group, GroupEnrollment, GroupMember, GroupStudentTask
from shared.unit_of_work import UnitOfWork


class GroupManagementService:
    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        with UnitOfWork(db, event_bus=event_bus) as uow:
            program = None
            if program_id is not None:
                program = group_repository.get_program_by_id(db, program_id)
                if not program:
                    raise PermissionDenied("Program not found")

            group = Group(title=title, description=description, program_id=program.id if program else None, created_by=ctx.user_id)
            group = group_repository.create(db, group)

            member = GroupMember(group_id=group.id, user_id=ctx.user_id, role=GroupRole.TEACHER.value)
            group_repository.create_member(db, member)

            uow.events.append(GroupCreatedEvent(group_id=group.id, created_by=ctx.user_id))
            return group

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        with UnitOfWork(db):
            group = group_repository.get_by_id(db, group_id)
            if not group:
                raise PermissionDenied("Group not found")

            try:
                GroupPolicy.require_manage_group(ctx, group)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to manage group") from exc

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise PermissionDenied("User not found")

            existing = group_repository.get_member(db, group_id=group_id, user_id=user_id)
            if existing:
                existing.role = role
                db.flush()
                return existing

            return group_repository.create_member(db, GroupMember(group_id=group_id, user_id=user_id, role=role))

    def add_teacher_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int):
        with UnitOfWork(db):
            group = group_repository.get_by_id(db, group_id)
            if not group:
                raise PermissionDenied("Group not found")

            try:
                GroupPolicy.require_manage_group(ctx, group)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to manage group") from exc

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise PermissionDenied("User not found")

            has_teacher_role = any(role_obj.role and role_obj.role.name == "teacher" for role_obj in user.roles)
            if not has_teacher_role:
                raise PermissionDenied("Only teacher users can be added to this group")

            role = GroupRole.TEACHER.value
            existing = group_repository.get_member(db, group_id=group_id, user_id=user_id)
            if existing:
                existing.role = role
                db.flush()
                return existing

            return group_repository.create_member(db, GroupMember(group_id=group_id, user_id=user_id, role=role))

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        with UnitOfWork(db, event_bus=event_bus) as uow:
            group = group_repository.get_by_id(db, group_id)
            if not group:
                raise PermissionDenied("Group not found")

            try:
                GroupPolicy.require_manage_group(ctx, group)
            except PermissionError as exc:
                raise PermissionDenied("Access denied to manage group") from exc

            existing = group_repository.get_enrollment(db, group_id=group_id, student_id=student_id)
            if existing:
                raise PermissionDenied("Student already enrolled")

            enrollment = group_repository.create_enrollment(db, GroupEnrollment(group_id=group_id, student_id=student_id, status="active"))

            if group.program_id:
                tasks = group_repository.list_program_tasks(db, program_id=group.program_id)
                group_repository.create_group_student_tasks(db, [GroupStudentTask(enrollment_id=enrollment.id, program_task_id=task.id, status="assigned") for task in tasks])

            uow.events.append(StudentEnrolledEvent(enrollment_id=enrollment.id, group_id=group.id, student_id=student_id))
            return enrollment


group_management_service = GroupManagementService()
