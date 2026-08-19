from sqlalchemy.orm import Session

from consultations.models.consultation_notification import ConsultationNotification


class ConsultationNotificationRepository:
    def create(self, db: Session, *, notification: ConsultationNotification):
        db.add(notification)
        db.flush()
        db.refresh(notification)
        return notification

    def list_for_recipient(self, db: Session, *, recipient_id: int):
        return (
            db.query(ConsultationNotification)
            .filter(ConsultationNotification.recipient_id == recipient_id)
            .order_by(ConsultationNotification.created_at.desc())
            .all()
        )


consultation_notification_repository = ConsultationNotificationRepository()
