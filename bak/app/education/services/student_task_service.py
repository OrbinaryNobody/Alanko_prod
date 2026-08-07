from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import EnrollmentNotFound, PermissionDenied, ProgramTaskNotFound, StudentTaskNotFound
from education.policies.student_task_policy import StudentTaskPolicy
from models.domains.education import GroupEnrollment, ProgramTask
from models.domains.student import StudentTask
from shared.unit_of_work import UnitOfWork


class StudentTaskService:
    def create_manual_task(self, db: Session, ctx: AccessContext, *, enrollment_id: int, program_task_id: int):
        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise EnrollmentNotFound("Enrollment not found")

        try:
            StudentTaskPolicy.require_create_manual_task(ctx, enrollment)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to this enrollment") from exc

        program_task = db.query(ProgramTask).filter(ProgramTask.id == program_task_id).first()
        if not program_task:
            raise ProgramTaskNotFound("Program task not found")

        with UnitOfWork(db):
            student_task = StudentTask(
                student_id=enrollment.student_id,
                task_id=program_task.task_id,
                status="manual_review",
            )
            db.add(student_task)
            db.flush()
            db.refresh(student_task)
            return student_task

    def update_task_grade(self, db: Session, ctx: AccessContext, *, task_id: int, grade: int, feedback: str | None):
        student_task = db.query(StudentTask).filter(StudentTask.id == task_id).first()
        if not student_task:
            raise StudentTaskNotFound("Student task not found")

        try:
            StudentTaskPolicy.require_grade(ctx, student_task, db)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to this student task") from exc

        with UnitOfWork(db):
            student_task.grade = grade
            student_task.feedback = feedback
            student_task.status = "graded"
            db.refresh(student_task)
            return student_task


student_task_service = StudentTaskService()
