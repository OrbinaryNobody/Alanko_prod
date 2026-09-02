from datetime import date, datetime

from sqlalchemy.orm import Session

from consultations.models.consultation_slot import ConsultationAccessMode, ConsultationSlot, ConsultationSlotStatus
from consultations.repositories.slot_repository import consultation_slot_repository
from consultations.timezone import to_utc
from core.config import settings
from core.exceptions import NotFoundError, ValidationError
from shared.unit_of_work import UnitOfWork


CONSULTATION_PRICES = {1: 900, 2: 600, 3: 500, 4: 450}


def consultation_price_for_booking(booked_count: int, capacity: int) -> int:
    participant_count = min(max(booked_count + 1, 1), capacity, 4)
    return CONSULTATION_PRICES[participant_count]


def consultation_price_for_participants(participant_count: int, capacity: int) -> int:
    current_count = min(max(participant_count, 1), capacity, 4)
    return CONSULTATION_PRICES[current_count]


class SlotService:
    @staticmethod
    def _slots_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
        return start_a < end_b and end_a > start_b

    def create_slot(
        self,
        db: Session,
        *,
        day_id: int,
        teacher_id: int,
        start_at: datetime,
        end_at: datetime,
        capacity: int = 4,
        price: int | None = None,
        currency: str = "RUB",
        access_mode: str = "PUBLIC",
        created_by: int | None = None,
    ):
        start_at = to_utc(start_at)
        end_at = to_utc(end_at)
        if start_at >= end_at:
            raise ValidationError("slot start time must be before end time")
        if capacity < 1 or capacity > settings.consultation_max_capacity:
            raise ValidationError(f"slot capacity must be between 1 and {settings.consultation_max_capacity}")

        if not settings.consultations_allow_overlapping_slots:
            for existing in consultation_slot_repository.list_for_day(db, day_id=day_id):
                if existing.status != ConsultationSlotStatus.ACTIVE.value or existing.teacher_id != teacher_id:
                    continue
                overlap = self._slots_overlap(start_at, end_at, existing.start_at, existing.end_at)
                if not overlap:
                    continue

                if access_mode == ConsultationAccessMode.PUBLIC.value and existing.access_mode == ConsultationAccessMode.INVITED.value:
                    raise ValidationError("Private consultation already occupies this time")
                if access_mode == ConsultationAccessMode.INVITED.value and existing.access_mode == ConsultationAccessMode.PUBLIC.value:
                    existing.status = ConsultationSlotStatus.CANCELLED.value
                    continue
                if access_mode == ConsultationAccessMode.INVITED.value and existing.access_mode == ConsultationAccessMode.INVITED.value:
                    raise ValidationError("Another private consultation already occupies this time")
                raise ValidationError("slot overlaps with an existing active consultation")

        slot = ConsultationSlot(
            day_id=day_id,
            teacher_id=teacher_id,
            start_at=start_at,
            end_at=end_at,
            capacity=capacity,
            price=settings.consultation_default_price if price is None else price,
            currency=currency.upper(),
            access_mode=access_mode,
            created_by=created_by,
        )
        with UnitOfWork(db):
            return consultation_slot_repository.create(db, slot=slot)

    def get_slot(self, db: Session, *, slot_id: int):
        return consultation_slot_repository.get_by_id(db, slot_id=slot_id)
    
    def list_slots(self, db: Session, *, date_from: date | None = None, date_to: date | None = None, limit: int = 100, offset: int = 0):
        return consultation_slot_repository.get_all(db, date_from=date_from, date_to=date_to, limit=limit, offset=offset)

    def get_price_quote(self, db: Session, *, slot_id: int) -> dict:
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("Consultation slot not found")
        from consultations.models.consultation_participant import ConsultationParticipant

        booked_count = db.query(ConsultationParticipant).filter(
            ConsultationParticipant.slot_id == slot.id,
            ConsultationParticipant.booking_status == "CONFIRMED",
        ).count()
        amount = consultation_price_for_booking(booked_count, slot.capacity)
        return {
            "slot_id": slot.id,
            "amount": amount,
            "currency": slot.currency,
            "payment_required": amount > 0,
            "booked_count": booked_count,
            "available_places": max(0, slot.capacity - booked_count),
        }

    def cancel_slot(self, db: Session, *, slot_id: int):
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("consultation slot not found")
        slot.status = "CANCELLED"
        db.flush()
        return slot
