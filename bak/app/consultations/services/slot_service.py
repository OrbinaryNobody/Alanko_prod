from datetime import datetime

from sqlalchemy.orm import Session

from consultations.models.consultation_slot import ConsultationSlot
from consultations.repositories.slot_repository import consultation_slot_repository
from core.config import settings
from core.exceptions import NotFoundError
from shared.unit_of_work import UnitOfWork


class SlotService:
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
        if start_at >= end_at:
            raise ValueError("slot start time must be before end time")
        if capacity < 1 or capacity > settings.consultation_max_capacity:
            raise ValueError(f"slot capacity must be between 1 and {settings.consultation_max_capacity}")

        if not settings.consultations_allow_overlapping_slots:
            for existing in consultation_slot_repository.list_for_day(db, day_id=day_id):
                if existing.status != "ACTIVE":
                    continue
                overlap = existing.start_at < end_at and existing.end_at > start_at
                if overlap:
                    raise ValueError("slot overlaps with an existing active consultation")

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
    
    def list_slots(self, db: Session):
        return consultation_slot_repository.get_all(db)

    def get_price_quote(self, db: Session, *, slot_id: int) -> dict:
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("Consultation slot not found")
        return {
            "slot_id": slot.id,
            "amount": slot.price,
            "currency": slot.currency,
            "payment_required": slot.price > 0,
        }

    def cancel_slot(self, db: Session, *, slot_id: int):
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise ValueError("consultation slot not found")
        slot.status = "CANCELLED"
        db.flush()
        return slot
