from datetime import date

from sqlalchemy.orm import Session

from consultations.models.consultation_slot import ConsultationSlot


class ConsultationSlotRepository:
    def get_by_id(self, db: Session, *, slot_id: int):
        return db.query(ConsultationSlot).filter(ConsultationSlot.id == slot_id).first()

    def get_by_id_for_update(self, db: Session, *, slot_id: int):
        return (
            db.query(ConsultationSlot)
            .filter(ConsultationSlot.id == slot_id)
            .with_for_update()
            .first()
        )

    def list_for_day(self, db: Session, *, day_id: int):
        return db.query(ConsultationSlot).filter(ConsultationSlot.day_id == day_id).all()
    
    def get_all(self, db: Session, *, date_from: date | None = None, date_to: date | None = None, limit: int = 100, offset: int = 0):
        query = db.query(ConsultationSlot)
        if date_from is not None:
            query = query.filter(ConsultationSlot.start_at >= date_from)
        if date_to is not None:
            query = query.filter(ConsultationSlot.start_at < date_to)
        return query.order_by(ConsultationSlot.start_at.asc()).offset(offset).limit(limit).all()

    def create(self, db: Session, *, slot: ConsultationSlot):
        db.add(slot)
        db.flush()
        db.refresh(slot)
        return slot

    def save(self, db: Session, *, slot: ConsultationSlot):
        db.add(slot)
        db.flush()
        db.refresh(slot)
        return slot


consultation_slot_repository = ConsultationSlotRepository()
