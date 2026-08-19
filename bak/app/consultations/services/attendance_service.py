from sqlalchemy.orm import Session

from consultations.models.consultation_participant import ConsultationAttendanceStatus, ConsultationBookingStatus
from consultations.policies.consultation_policy import consultation_policy
from consultations.repositories.participant_repository import consultation_participant_repository
from consultations.repositories.slot_repository import consultation_slot_repository
from core.access import AccessContext
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from shared.unit_of_work import UnitOfWork


class AttendanceService:
    def list_for_slot(self, db: Session, *, ctx: AccessContext, slot_id: int):
        slot = consultation_slot_repository.get_by_id(db, slot_id=slot_id)
        if not slot:
            raise NotFoundError("Consultation slot not found")

        try:
            consultation_policy.require_manage_slot(ctx, slot)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc

        return consultation_participant_repository.list_for_slot(db, slot_id=slot_id)

    def set_status(self, db: Session, *, ctx: AccessContext, participant_id: int, status: str):
        if status not in {
            ConsultationAttendanceStatus.PRESENT.value,
            ConsultationAttendanceStatus.ABSENT.value,
        }:
            raise ConflictError("Unsupported attendance status")

        with UnitOfWork(db):
            participant = consultation_participant_repository.get_by_id(db, participant_id=participant_id)
            if not participant:
                raise NotFoundError("Consultation participant not found")
            if participant.booking_status != ConsultationBookingStatus.CONFIRMED.value:
                raise ConflictError("Attendance can be marked only for a confirmed participant")

            slot = consultation_slot_repository.get_by_id(db, slot_id=participant.slot_id)
            if not slot:
                raise NotFoundError("Consultation slot not found")

            try:
                consultation_policy.require_manage_slot(ctx, slot)
            except PermissionError as exc:
                raise PermissionDenied(str(exc)) from exc

            participant.attendance_status = status
            db.flush()
            return participant


attendance_service = AttendanceService()
