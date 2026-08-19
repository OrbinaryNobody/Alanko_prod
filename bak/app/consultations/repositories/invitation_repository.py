from sqlalchemy.orm import Session

from consultations.models.consultation_invitation import ConsultationInvitation


class ConsultationInvitationRepository:
    def get_by_id(self, db: Session, *, invitation_id: int):
        return db.query(ConsultationInvitation).filter(ConsultationInvitation.id == invitation_id).first()

    def get_by_id_for_update(self, db: Session, *, invitation_id: int):
        return (
            db.query(ConsultationInvitation)
            .filter(ConsultationInvitation.id == invitation_id)
            .with_for_update()
            .first()
        )

    def list_for_student(self, db: Session, *, student_id: int):
        return (
            db.query(ConsultationInvitation)
            .filter(ConsultationInvitation.student_id == student_id)
            .order_by(ConsultationInvitation.created_at.desc())
            .all()
        )

    def get_for_slot_student(self, db: Session, *, slot_id: int, student_id: int):
        return (
            db.query(ConsultationInvitation)
            .filter(
                ConsultationInvitation.slot_id == slot_id,
                ConsultationInvitation.student_id == student_id,
            )
            .order_by(ConsultationInvitation.created_at.desc())
            .first()
        )

    def create(self, db: Session, *, invitation: ConsultationInvitation):
        db.add(invitation)
        db.flush()
        db.refresh(invitation)
        return invitation


consultation_invitation_repository = ConsultationInvitationRepository()
