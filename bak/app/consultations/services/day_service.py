from datetime import date, datetime, time

from sqlalchemy.orm import Session

from consultations.models.consultation_day import ConsultationDay, ConsultationDayStatus
from consultations.repositories.day_repository import consultation_day_repository
from shared.unit_of_work import UnitOfWork
from core.exceptions import ConflictError, NotFoundError, ValidationError


class DayService:
    def create_day(self, db: Session, *, date_value: date, status: str = "OPEN", available_from: time | None = None, available_to: time | None = None):
        existing = consultation_day_repository.get_by_date(db, target_date=date_value)
        if existing:
            raise ConflictError(f"Day already exists for {date_value}")

        day = ConsultationDay(
            date=date_value,
            status=status,
            available_from=available_from,
            available_to=available_to,
        )
        with UnitOfWork(db):
            return consultation_day_repository.create(db, day=day)

    def get_day(self, db: Session, *, day_id: int):
        return consultation_day_repository.get_by_id(db, day_id=day_id)
    
    def list_days(self, db: Session, *, date_from: date | None = None, date_to: date | None = None):
        return consultation_day_repository.get_all(db, date_from=date_from, date_to=date_to)

    def set_status(self, db: Session, *, day_id: int, status: str):
        day = consultation_day_repository.get_by_id(db, day_id=day_id)
        if not day:
            raise NotFoundError("Consultation day not found")

        allowed = {ConsultationDayStatus.OPEN.value, ConsultationDayStatus.CLOSED.value}
        if status not in allowed:
            raise ValidationError("Unsupported consultation day status")

        day.status = status
        day.updated_at = datetime.utcnow()
        db.flush()
        return day

    def set_working_window(self, db: Session, *, day_id: int, available_from: time | None, available_to: time | None):
        day = consultation_day_repository.get_by_id(db, day_id=day_id)
        if not day:
            raise NotFoundError("Consultation day not found")
        day.available_from = available_from
        day.available_to = available_to
        day.updated_at = datetime.utcnow()
        db.flush()
        return day
