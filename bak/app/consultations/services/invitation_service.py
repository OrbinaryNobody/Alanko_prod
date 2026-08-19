from datetime import datetime, timezone

from sqlalchemy.orm import Session

from accounts.facade import accounts_facade
from consultations.models.consultation_invitation import ConsultationInvitation, ConsultationInvitationStatus
from consultations.models.consultation_participant import (
    ConsultationBookingStatus,
    ConsultationParticipant,
    ConsultationParticipantSource,
)
from consultations.models.consultation_slot import ConsultationSlotStatus
from consultations.policies.consultation_policy import consultation_policy
from consultations.repositories.day_repository import consultation_day_repository
from consultations.repositories.invitation_repository import consultation_invitation_repository
from consultations.repositories.participant_repository import consultation_participant_repository
from consultations.repositories.slot_repository import consultation_slot_repository
from consultations.services.notification_service import notification_service
from core.access import AccessContext
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from shared.unit_of_work import UnitOfWork


class InvitationService:
    def _ensure_booking_window_is_open(self, slot) -> None:
        now = datetime.now(timezone.utc)
        if slot.booking_open_at is not None:
            booking_open_at = slot.booking_open_at
            if booking_open_at.tzinfo is None:
                booking_open_at = booking_open_at.replace(tzinfo=timezone.utc)
            if now < booking_open_at:
                raise ConflictError("Consultation booking is not open yet")
        if slot.booking_close_at is not None:
            booking_close_at = slot.booking_close_at
            if booking_close_at.tzinfo is None:
                booking_close_at = booking_close_at.replace(tzinfo=timezone.utc)
            if now > booking_close_at:
                raise ConflictError("Consultation booking is closed")

    def create_invitations(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        slot_id: int,
        student_ids: list[int],
    ) -> list[ConsultationInvitation]:
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("Consultation slot not found")
        if slot.status != ConsultationSlotStatus.ACTIVE.value:
            raise ConflictError("Cannot invite students to an inactive consultation slot")

        try:
            consultation_policy.require_manage_slot(ctx, slot)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc

        invitations: list[ConsultationInvitation] = []
        unique_student_ids = list(dict.fromkeys(student_ids))
        with UnitOfWork(db):
            for student_id in unique_student_ids:
                if not accounts_facade.is_student(db, user_id=student_id):
                    raise NotFoundError(f"Student {student_id} not found")

                existing = consultation_invitation_repository.get_for_slot_student(
                    db,
                    slot_id=slot_id,
                    student_id=student_id,
                )
                if existing and existing.status in {
                    ConsultationInvitationStatus.PENDING.value,
                    ConsultationInvitationStatus.ACCEPTED.value,
                }:
                    invitations.append(existing)
                    continue

                invitation = consultation_invitation_repository.create(
                    db,
                    invitation=ConsultationInvitation(
                        slot_id=slot_id,
                        student_id=student_id,
                        invited_by=ctx.user_id,
                        status=ConsultationInvitationStatus.PENDING.value,
                    ),
                )
                notification_service.create_invitation_notification(
                    db,
                    invitation_id=invitation.id,
                    student_id=student_id,
                )
                invitations.append(invitation)

        return invitations

    def list_for_student(self, db: Session, *, student_id: int) -> list[ConsultationInvitation]:
        return consultation_invitation_repository.list_for_student(db, student_id=student_id)

    def accept(self, db: Session, *, student_id: int, invitation_id: int):
        with UnitOfWork(db):
            invitation = consultation_invitation_repository.get_by_id_for_update(db, invitation_id=invitation_id)
            if not invitation:
                raise NotFoundError("Consultation invitation not found")
            if invitation.student_id != student_id:
                raise PermissionDenied("Invitation does not belong to this student")
            if invitation.status != ConsultationInvitationStatus.PENDING.value:
                raise ConflictError("Consultation invitation has already been answered")

            slot = consultation_slot_repository.get_by_id_for_update(db, slot_id=invitation.slot_id)
            if not slot:
                raise NotFoundError("Consultation slot not found")
            if slot.status != ConsultationSlotStatus.ACTIVE.value:
                raise ConflictError("Consultation slot is not active")
            self._ensure_booking_window_is_open(slot)

            day = consultation_day_repository.get_by_id(db, day_id=slot.day_id)
            if not day or day.status != "OPEN":
                raise ConflictError("Consultation day is closed")

            existing = consultation_participant_repository.get_for_slot_student(
                db,
                slot_id=slot.id,
                student_id=student_id,
            )
            if existing and existing.booking_status == ConsultationBookingStatus.CONFIRMED.value:
                raise ConflictError("Student is already booked for this consultation")

            if consultation_participant_repository.count_confirmed_for_slot(db, slot_id=slot.id) >= slot.capacity:
                raise ConflictError("Consultation slot is full")

            if existing:
                existing.booking_status = ConsultationBookingStatus.CONFIRMED.value
                existing.source = ConsultationParticipantSource.INVITATION.value
                existing.cancelled_at = None
                participant = existing
            else:
                participant = consultation_participant_repository.create(
                    db,
                    participant=ConsultationParticipant(
                        slot_id=slot.id,
                        student_id=student_id,
                        source=ConsultationParticipantSource.INVITATION.value,
                        booking_status=ConsultationBookingStatus.CONFIRMED.value,
                    ),
                )

            invitation.status = ConsultationInvitationStatus.ACCEPTED.value
            invitation.responded_at = datetime.now(timezone.utc)
            db.flush()
            return participant

    def decline(self, db: Session, *, student_id: int, invitation_id: int):
        with UnitOfWork(db):
            invitation = consultation_invitation_repository.get_by_id_for_update(db, invitation_id=invitation_id)
            if not invitation:
                raise NotFoundError("Consultation invitation not found")
            if invitation.student_id != student_id:
                raise PermissionDenied("Invitation does not belong to this student")
            if invitation.status != ConsultationInvitationStatus.PENDING.value:
                raise ConflictError("Consultation invitation has already been answered")

            invitation.status = ConsultationInvitationStatus.DECLINED.value
            invitation.responded_at = datetime.now(timezone.utc)
            db.flush()
            return invitation


invitation_service = InvitationService()
