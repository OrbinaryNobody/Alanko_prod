from datetime import date, datetime

from sqlalchemy.orm import Session

from consultations.models.consultation_day import ConsultationDay
from consultations.models.consultation_participant import ConsultationParticipant
from consultations.models.consultation_slot import ConsultationSlot
from models.domains.auth import User
from consultations.timezone import serialize_local
from consultations.services.slot_service import consultation_price_for_booking


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
            all_day_slots = db.query(ConsultationSlot).filter(
                ConsultationSlot.day_id == day.id,
                ConsultationSlot.status == "ACTIVE",
            ).all()
            private_windows = [
                slot for slot in all_day_slots
                if slot.access_mode == "INVITED"
            ]
            for slot in all_day_slots:
                if slot.access_mode != "PUBLIC":
                    continue
                if any(
                    other.id != slot.id
                    and other.teacher_id == slot.teacher_id
                    and other.access_mode == "INVITED"
                    and other.start_at < slot.end_at
                    and other.end_at > slot.start_at
                    for other in private_windows
                ):
                    continue
                teacher = db.query(User).filter(User.id == slot.teacher_id).first()
                booked_count = db.query(ConsultationParticipant).filter(
                    ConsultationParticipant.slot_id == slot.id,
                    ConsultationParticipant.booking_status == "CONFIRMED",
                ).count()
                is_booked = bool(student_id and db.query(ConsultationParticipant).filter(
                    ConsultationParticipant.slot_id == slot.id,
                    ConsultationParticipant.student_id == student_id,
                    ConsultationParticipant.booking_status == "CONFIRMED",
                ).first())
                result.append({
                    "slot_id": slot.id,
                    "day_id": slot.day_id,
                    "teacher_id": slot.teacher_id,
                    "teacher_name": f"{teacher.first_name} {teacher.last_name or ''}".strip() if teacher else f"Преподаватель #{slot.teacher_id}",
                    "start_at": serialize_local(slot.start_at),
                    "end_at": serialize_local(slot.end_at),
                    "capacity": slot.capacity,
                    "price": consultation_price_for_booking(booked_count, slot.capacity),
                    "currency": slot.currency,
                    "payment_required": slot.price > 0,
                    "access_mode": slot.access_mode,
                    "status": slot.status,
                    "booked_count": booked_count,
                    "available_places": max(0, slot.capacity - booked_count),
                    "is_last_spot": slot.capacity - booked_count == 1,
                    "is_booked": is_booked,
                })
        return result
