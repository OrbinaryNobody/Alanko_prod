from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.policies.group_policy import GroupPolicy
from education.repositories.group_repository import group_repository
from education.services.group_management_service import group_management_service


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


group_service = GroupService()
