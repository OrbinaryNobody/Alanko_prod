from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from consultations.models.consultation_day import ConsultationDay, ConsultationDayStatus
from consultations.repositories.day_repository import consultation_day_repository
from consultations.models.consultation_participant import ConsultationParticipant
from consultations.models.consultation_slot import ConsultationSlot, ConsultationSlotStatus
from consultations.timezone import to_local, to_utc
from shared.unit_of_work import UnitOfWork
from core.exceptions import ConflictError, NotFoundError, ValidationError


class DayService:
    def create_day(self, db: Session, *, date_value: date, teacher_id: int | None = None, status: str = "OPEN", available_from: time | None = None, available_to: time | None = None):
        existing = consultation_day_repository.get_by_date(db, target_date=date_value)
        if existing:
            raise ConflictError(f"Day already exists for {date_value}")

        day = ConsultationDay(
            date=date_value,
            teacher_id=teacher_id,
            status=status,
            available_from=available_from,
            available_to=available_to,
        )
        with UnitOfWork(db):
            day = consultation_day_repository.create(db, day=day)
            self._sync_generated_slots(db, day)
            return day

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

    def set_working_window(self, db: Session, *, day_id: int, teacher_id: int | None, status: str, available_from: time | None, available_to: time | None):
        with UnitOfWork(db):
            day = consultation_day_repository.get_by_id(db, day_id=day_id)
            if not day:
                raise NotFoundError("Consultation day not found")
            if status not in {ConsultationDayStatus.OPEN.value, ConsultationDayStatus.CLOSED.value}:
                raise ValidationError("Unsupported consultation day status")
            if teacher_id is not None:
                day.teacher_id = teacher_id
                day.status = status
            day.available_from = available_from
            day.available_to = available_to
            day.updated_at = datetime.utcnow()
            db.flush()
            self._sync_generated_slots(db, day)
            return day

    def _sync_generated_slots(self, db: Session, day: ConsultationDay) -> None:
        if day.available_from and day.available_to and day.available_from >= day.available_to:
            raise ValidationError("available_from must be before available_to")

        slot_starts = []
        if day.teacher_id and day.available_from and day.available_to and day.status == ConsultationDayStatus.OPEN.value:
            window_start = datetime.combine(day.date, day.available_from)
            window_end = datetime.combine(day.date, day.available_to)
            current = window_start
            while current + timedelta(hours=2) <= window_end:
                slot_starts.append(current.time())
                current += timedelta(hours=2)

        existing_generated = db.query(ConsultationSlot).filter(
            ConsultationSlot.day_id == day.id,
            ConsultationSlot.status == ConsultationSlotStatus.ACTIVE.value,
        ).all()
        desired = {(start, (datetime.combine(day.date, start) + timedelta(hours=2)).time()) for start in slot_starts}
        for slot in existing_generated:
            local_start = to_local(slot.start_at)
            local_end = to_local(slot.end_at)
            key = (local_start.time(), local_end.time())
            slot_outside_window = (
                not day.available_from
                or not day.available_to
                or local_start.time() < day.available_from
                or local_end.time() > day.available_to
            )
            if (key not in desired or slot.teacher_id != day.teacher_id or slot_outside_window) and not db.query(ConsultationParticipant).filter(
                ConsultationParticipant.slot_id == slot.id,
                ConsultationParticipant.booking_status == "CONFIRMED",
            ).first():
                slot.status = ConsultationSlotStatus.CANCELLED.value

        for start_time, end_time in desired:
            exists = db.query(ConsultationSlot).filter(
                ConsultationSlot.day_id == day.id,
                ConsultationSlot.teacher_id == day.teacher_id,
                ConsultationSlot.start_at == to_utc(datetime.combine(day.date, start_time)),
                ConsultationSlot.end_at == to_utc(datetime.combine(day.date, end_time)),
                ConsultationSlot.status == ConsultationSlotStatus.ACTIVE.value,
            ).first()
            if not exists:
                db.add(ConsultationSlot(
                    day_id=day.id,
                    teacher_id=day.teacher_id,
                    start_at=to_utc(datetime.combine(day.date, start_time)),
                    end_at=to_utc(datetime.combine(day.date, end_time)),
                    capacity=4,
                    price=0,
                    access_mode="PUBLIC",
                    generated_by_window=True,
                ))
        db.flush()
