from datetime import date

from sqlalchemy.orm import Session

from consultations.models.consultation_day import ConsultationDay


class ConsultationDayRepository:
    def get_all(self, db: Session, *, date_from: date | None = None, date_to: date | None = None):
        query = db.query(ConsultationDay)
        if date_from is not None:
            query = query.filter(ConsultationDay.date >= date_from)
        if date_to is not None:
            query = query.filter(ConsultationDay.date <= date_to)
        return query.order_by(ConsultationDay.date.asc()).all()

    def get_by_id(self, db: Session, *, day_id: int):
        return db.query(ConsultationDay).filter(ConsultationDay.id == day_id).first()

    def get_by_date(self, db: Session, *, target_date: date):
        return db.query(ConsultationDay).filter(ConsultationDay.date == target_date).first()

    def create(self, db: Session, *, day: ConsultationDay):
        db.add(day)
        db.flush()
        db.refresh(day)
        return day

    def save(self, db: Session, *, day: ConsultationDay):
        db.add(day)
        db.flush()
        db.refresh(day)
        return day


consultation_day_repository = ConsultationDayRepository()
