from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import GroupEnrollment, GroupStudentTask, ProgramTask


class StudentTaskService:
    def create_manual_task(self, db: Session, *, enrollment_id: int, program_task_id: int):
        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

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

    def update_task_grade(self, db: Session, *, task_id: int, grade: int, feedback: str | None):
        task = db.query(GroupStudentTask).filter(GroupStudentTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Student task not found")

        task.grade = grade
        task.feedback = feedback
        task.status = "checked"
        task.checked_at = None
        db.commit()
        db.refresh(task)
        return task


student_task_service = StudentTaskService()
