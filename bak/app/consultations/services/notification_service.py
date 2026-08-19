from sqlalchemy.orm import Session

from consultations.models.consultation_notification import ConsultationNotification
from consultations.repositories.notification_repository import consultation_notification_repository


class NotificationService:
    def create_invitation_notification(self, db: Session, *, invitation_id: int, student_id: int):
        return consultation_notification_repository.create(
            db,
            notification=ConsultationNotification(
                recipient_id=student_id,
                invitation_id=invitation_id,
                notification_type="CONSULTATION_INVITATION",
                title="New consultation invitation",
                body="You have been invited to a private consultation. Please accept or decline the invitation.",
            ),
        )

    def list_for_student(self, db: Session, *, student_id: int):
        return consultation_notification_repository.list_for_recipient(db, recipient_id=student_id)


notification_service = NotificationService()
