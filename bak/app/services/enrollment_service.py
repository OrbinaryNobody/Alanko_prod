from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import GroupEnrollment


class EnrollmentService:
    def enroll_student(self, db: Session, *, group_id: int, student_id: int):
        existing = db.query(GroupEnrollment).filter(GroupEnrollment.group_id == group_id, GroupEnrollment.student_id == student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student already enrolled")

        enrollment = GroupEnrollment(group_id=group_id, student_id=student_id, status="active")
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    def remove_student(self, db: Session, *, enrollment_id: int):
        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        enrollment.status = "left"
        enrollment.left_at = None
        db.commit()
        return enrollment

    def graduate_student(self, db: Session, *, enrollment_id: int):
        enrollment = db.query(GroupEnrollment).filter(GroupEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        enrollment.status = "completed"
        db.commit()
        return enrollment


enrollment_service = EnrollmentService()
