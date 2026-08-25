from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from consultations.models.consultation_participant import ConsultationParticipant, ConsultationParticipantSource, ConsultationBookingStatus
from consultations.models.consultation_slot import ConsultationAccessMode, ConsultationSlotStatus
from consultations.repositories.day_repository import consultation_day_repository
from consultations.repositories.participant_repository import consultation_participant_repository
from consultations.repositories.slot_repository import consultation_slot_repository
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from shared.unit_of_work import UnitOfWork


class BookingService:
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

    def get_my_bookings(self, db: Session, *, student_id: int):
        return consultation_participant_repository.list_confirmed_for_student(db, student_id=student_id)

    def book_slot(self, db: Session, *, student_id: int, slot_id: int):
        with UnitOfWork(db):
            slot = consultation_slot_repository.get_by_id_for_update(db, slot_id=slot_id)
            if not slot:
                raise NotFoundError("Consultation slot not found")
            if slot.status != ConsultationSlotStatus.ACTIVE.value:
                raise ConflictError("Consultation slot is not active")
            if slot.access_mode == ConsultationAccessMode.INVITED.value:
                raise PermissionDenied("This consultation requires an accepted invitation")
            self._ensure_booking_window_is_open(slot)

            day = consultation_day_repository.get_by_id(db, day_id=slot.day_id)
            if not day or day.status != "OPEN":
                raise ConflictError("Consultation day is closed")

            existing = consultation_participant_repository.get_for_slot_student(db, slot_id=slot_id, student_id=student_id)
            if existing and existing.booking_status == ConsultationBookingStatus.CONFIRMED.value:
                raise ConflictError("Student already booked this slot")

            confirmed_count = consultation_participant_repository.count_confirmed_for_slot(db, slot_id=slot_id)
            if confirmed_count >= slot.capacity:
                raise ConflictError("Consultation slot is full")

            if existing:
                existing.booking_status = ConsultationBookingStatus.CONFIRMED.value
                existing.source = ConsultationParticipantSource.SELF.value
                existing.cancelled_at = None
                db.flush()
                return existing

            participant = ConsultationParticipant(
                slot_id=slot_id,
                student_id=student_id,
                source=ConsultationParticipantSource.SELF.value,
                booking_status=ConsultationBookingStatus.CONFIRMED.value,
            )
            try:
                return consultation_participant_repository.create(db, participant=participant)
            except IntegrityError as exc:
                raise ConflictError("Student already booked this slot") from exc

    def cancel_booking(self, db: Session, *, student_id: int, participant_id: int):
        participant = consultation_participant_repository.get_by_id(db, participant_id=participant_id)
        if not participant:
            raise NotFoundError("Consultation participant not found")
        if participant.student_id != student_id:
            raise PermissionDenied("Participant does not belong to this student")
        with UnitOfWork(db):
            participant.booking_status = ConsultationBookingStatus.CANCELLED.value
            participant.cancelled_at = datetime.utcnow()
            db.flush()
            return participant
