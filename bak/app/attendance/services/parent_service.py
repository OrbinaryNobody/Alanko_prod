from sqlalchemy.orm import Session

from attendance.repositories.attendance_repository import attendance_repository
from core.exceptions import ConflictError
from models.domains.attendance import ParentGuardian, StudentParent
from shared.unit_of_work import UnitOfWork


class ParentService:
    def attach_parent(self, db: Session, *, student_id: int, first_name: str, last_name: str, middle_name: str | None, phone: str, email: str | None = None):
        with UnitOfWork(db):
            parent = ParentGuardian(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                phone=phone,
                email=email,
            )
            db.add(parent)
            db.flush()
            db.add(StudentParent(student_id=student_id, parent_id=parent.id, is_primary=1))
            db.flush()
            return parent


parent_service = ParentService()