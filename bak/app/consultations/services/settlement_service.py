from datetime import datetime, timezone

from sqlalchemy.orm import Session

from consultations.models.consultation_participant import (
    ConsultationAttendanceStatus,
    ConsultationBookingStatus,
    ConsultationPaymentStatus,
)
from consultations.policies.consultation_policy import consultation_policy
from consultations.repositories.participant_repository import consultation_participant_repository
from consultations.repositories.slot_repository import consultation_slot_repository
from core.access import AccessContext
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from shared.unit_of_work import UnitOfWork


class SettlementService:
    def _get_slot_for_manager(self, db: Session, *, ctx: AccessContext, slot_id: int):
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("Consultation slot not found")
        try:
            consultation_policy.require_manage_slot(ctx, slot)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        return slot

    def set_payment_status(self, db: Session, *, ctx: AccessContext, participant_id: int, status: str):
        if status not in {ConsultationPaymentStatus.PAID.value, ConsultationPaymentStatus.UNPAID.value}:
            raise ConflictError("Unsupported consultation payment status")

        with UnitOfWork(db):
            participant = consultation_participant_repository.get_by_id(db, participant_id=participant_id)
            if not participant:
                raise NotFoundError("Consultation participant not found")
            self._get_slot_for_manager(db, ctx=ctx, slot_id=participant.slot_id)

            if participant.booking_status != ConsultationBookingStatus.CONFIRMED.value:
                raise ConflictError("Payment can be recorded only for a confirmed participant")
            if participant.attendance_status != ConsultationAttendanceStatus.PRESENT.value:
                raise ConflictError("Payment can be recorded only for a student marked PRESENT")

            participant.payment_status = status
            participant.paid_at = datetime.now(timezone.utc) if status == ConsultationPaymentStatus.PAID.value else None
            db.flush()
            return participant

    def get_summary(self, db: Session, *, ctx: AccessContext, slot_id: int) -> dict:
        slot = self._get_slot_for_manager(db, ctx=ctx, slot_id=slot_id)
        participants = consultation_participant_repository.list_for_slot(db, slot_id=slot_id)
        confirmed = [
            participant
            for participant in participants
            if participant.booking_status == ConsultationBookingStatus.CONFIRMED.value
        ]
        present = [
            participant
            for participant in confirmed
            if participant.attendance_status == ConsultationAttendanceStatus.PRESENT.value
        ]
        paid = [
            participant
            for participant in present
            if participant.payment_status == ConsultationPaymentStatus.PAID.value
        ]
        return {
            "slot_id": slot_id,
            "currency": slot.currency,
            "confirmed_children": len(confirmed),
            "present_children": len(present),
            "paid_children": len(paid),
            "unpaid_children": len(present) - len(paid),
            "price_per_child": slot.price,
            "total_due": len(present) * slot.price,
            "total_paid": len(paid) * slot.price,
            "total_unpaid": (len(present) - len(paid)) * slot.price,
        }


settlement_service = SettlementService()
