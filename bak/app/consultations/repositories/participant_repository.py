from sqlalchemy.orm import Session

from consultations.models.consultation_participant import ConsultationParticipant


class ConsultationParticipantRepository:
    def get_by_id(self, db: Session, *, participant_id: int):
        return db.query(ConsultationParticipant).filter(ConsultationParticipant.id == participant_id).first()

    def get_for_slot_student(self, db: Session, *, slot_id: int, student_id: int):
        return (
            db.query(ConsultationParticipant)
            .filter(
                ConsultationParticipant.slot_id == slot_id,
                ConsultationParticipant.student_id == student_id,
            )
            .first()
        )

    def list_for_slot(self, db: Session, *, slot_id: int):
        return db.query(ConsultationParticipant).filter(ConsultationParticipant.slot_id == slot_id).all()

    def count_confirmed_for_slot(self, db: Session, *, slot_id: int) -> int:
        return (
            db.query(ConsultationParticipant)
            .filter(
                ConsultationParticipant.slot_id == slot_id,
                ConsultationParticipant.booking_status == "CONFIRMED",
            )
            .count()
        )

    def list_confirmed_for_student(self, db: Session, *, student_id: int):
        return (
            db.query(ConsultationParticipant)
            .filter(
                ConsultationParticipant.student_id == student_id,
                ConsultationParticipant.booking_status == "CONFIRMED",
            )
            .order_by(ConsultationParticipant.booked_at.desc())
            .all()
        )

    def create(self, db: Session, *, participant: ConsultationParticipant):
        db.add(participant)
        db.flush()
        db.refresh(participant)
        return participant

    def save(self, db: Session, *, participant: ConsultationParticipant):
        db.add(participant)
        db.flush()
        db.refresh(participant)
        return participant


consultation_participant_repository = ConsultationParticipantRepository()
