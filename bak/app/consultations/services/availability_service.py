from datetime import date, datetime

from sqlalchemy.orm import Session

from consultations.models.consultation_day import ConsultationDay
from consultations.models.consultation_slot import ConsultationSlot


class AvailabilityService:
    def get_available_slots(self, db: Session, *, student_id: int | None = None, date_from: date | None = None, date_to: date | None = None):
        if date_from is None:
            date_from = datetime.utcnow().date()
        if date_to is None:
            date_to = date_from

        days = db.query(ConsultationDay).filter(ConsultationDay.date >= date_from, ConsultationDay.date <= date_to).all()
        result = []
        for day in days:
            if day.status != "OPEN":
                continue
            slots = db.query(ConsultationSlot).filter(ConsultationSlot.day_id == day.id, ConsultationSlot.status == "ACTIVE").all()
            for slot in slots:
                result.append({
                    "slot_id": slot.id,
                    "day_id": slot.day_id,
                    "teacher_id": slot.teacher_id,
                    "start_at": slot.start_at.isoformat() if slot.start_at else None,
                    "end_at": slot.end_at.isoformat() if slot.end_at else None,
                    "capacity": slot.capacity,
                    "price": slot.price,
                    "currency": slot.currency,
                    "payment_required": slot.price > 0,
                    "access_mode": slot.access_mode,
                    "status": slot.status,
                })
        return result
