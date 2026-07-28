from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.policies.student_task_policy import StudentTaskPolicy
from models import Group, GroupEnrollment, GroupStudentTask, ProgramTask


class StudentTaskService:
    def _find_enrollment(self, db: Session, enrollment_id: int) -> GroupEnrollment:
        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return enrollment

    def _find_task(self, db: Session, task_id: int) -> GroupStudentTask:
        task = db.query(GroupStudentTask).filter(GroupStudentTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Student task not found")
        return task

    def create_manual_task(
        self,
        db: Session,
        ctx: AccessContext,
        *,
        enrollment_id: int,
        program_task_id: int,
    ):
        enrollment = self._find_enrollment(db, enrollment_id)
        try:
            StudentTaskPolicy.require_create_manual_task(ctx, enrollment)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        program_task = db.query(ProgramTask).filter(ProgramTask.id == program_task_id).first()
        if not program_task:
            raise HTTPException(status_code=404, detail="Program task not found")

        existing = db.query(GroupStudentTask).filter(
            GroupStudentTask.enrollment_id == enrollment_id,
            GroupStudentTask.program_task_id == program_task_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student task already exists")

        task = GroupStudentTask(enrollment_id=enrollment.id, program_task_id=program_task.id, status="assigned")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task_grade(
        self,
        db: Session,
        ctx: AccessContext,
        *,
        task_id: int,
        grade: int,
        feedback: str | None,
    ):
        task = self._find_task(db, task_id)
        try:
            StudentTaskPolicy.require_grade(ctx, task, db)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        task.grade = grade
        task.feedback = feedback
        task.status = "checked"
        task.checked_at = None
        db.commit()
        db.refresh(task)
        return task


student_task_service = StudentTaskService()
