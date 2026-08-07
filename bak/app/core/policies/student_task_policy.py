from core.access import AccessContext
from models.domains.education import GroupEnrollment, GroupStudentTask
from sqlalchemy.orm import Session


class StudentTaskPolicy:
    @staticmethod
    def require_grade(ctx: AccessContext, student_task: GroupStudentTask, db: Session) -> None:
        if ctx.is_admin:
            return

        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == student_task.enrollment_id).first()
        if not enrollment:
            raise PermissionError("Access denied: task enrollment not found")

        if enrollment.group and ctx.can_manage(enrollment.group.created_by):
            return

        if any(member.user_id == ctx.user_id for member in enrollment.group.members):
            return

        raise PermissionError("Access denied: grade student task")

    @staticmethod
    def require_create_manual_task(ctx: AccessContext, enrollment: GroupEnrollment) -> None:
        if ctx.is_admin:
            return

        if enrollment.group and ctx.can_manage(enrollment.group.created_by):
            return

        if any(member.user_id == ctx.user_id for member in enrollment.group.members):
            return

        raise PermissionError("Access denied: create manual task")
