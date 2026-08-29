from sqlalchemy.orm import Session
from sqlalchemy import func

from consultations.services.availability_service import AvailabilityService
from consultations.services.attendance_service import AttendanceService
from consultations.services.booking_service import BookingService
from consultations.services.day_service import DayService
from consultations.services.invitation_service import InvitationService
from consultations.services.notification_service import NotificationService
from consultations.services.slot_service import SlotService
from consultations.services.settlement_service import SettlementService
from consultations.models.consultation_slot import ConsultationSlot
from models.domains.auth import User
from consultations.timezone import serialize_local
from consultations.models.consultation_participant import ConsultationParticipant
from consultations.services.slot_service import consultation_price_for_participants


class ConsultationsFacade:
    def __init__(self):
        self.day_service = DayService()
        self.slot_service = SlotService()
        self.booking_service = BookingService()
        self.availability_service = AvailabilityService()
        self.invitation_service = InvitationService()
        self.attendance_service = AttendanceService()
        self.notification_service = NotificationService()
        self.settlement_service = SettlementService()

    def create_day(self, db: Session, *, date, teacher_id=None, status="OPEN", available_from=None, available_to=None):
        return self.day_service.create_day(db, date_value=date, teacher_id=teacher_id, status=status, available_from=available_from, available_to=available_to)

    def get_day(self, db: Session, *, day_id: int):
        return self.day_service.get_day(db, day_id=day_id)
    
    def list_days(self, db: Session, *, date_from=None, date_to=None):
        return self.day_service.list_days(db, date_from=date_from, date_to=date_to)

    def set_day_status(self, db: Session, *, day_id: int, status: str):
        return self.day_service.set_status(db, day_id=day_id, status=status)

    def set_day_working_window(self, db: Session, *, day_id: int, teacher_id: int, status: str, available_from=None, available_to=None):
        return self.day_service.set_working_window(db, day_id=day_id, teacher_id=teacher_id, status=status, available_from=available_from, available_to=available_to)

    def create_slot(self, db: Session, *, day_id: int, teacher_id: int, start_at, end_at, capacity=4, price=None, currency="RUB", access_mode="PUBLIC", created_by=None):
        return self.slot_service.create_slot(
            db,
            day_id=day_id,
            teacher_id=teacher_id,
            start_at=start_at,
            end_at=end_at,
            capacity=capacity,
            price=price,
            currency=currency,
            access_mode=access_mode,
            created_by=created_by,
        )
    
    def list_slots(self, db: Session, *, date_from=None, date_to=None, limit: int = 100, offset: int = 0):
        return self.slot_service.list_slots(db, date_from=date_from, date_to=date_to, limit=limit, offset=offset)

    def get_price_quote(self, db: Session, *, slot_id: int):
        return self.slot_service.get_price_quote(db, slot_id=slot_id)

    def get_available_slots(self, db: Session, *, student_id: int | None = None, date_from=None, date_to=None):
        return self.availability_service.get_available_slots(db, student_id=student_id, date_from=date_from, date_to=date_to)

    def book_slot(self, db: Session, *, student_id: int, slot_id: int):
        return self.booking_service.book_slot(db, student_id=student_id, slot_id=slot_id)

    def get_my_bookings(self, db: Session, *, student_id: int):
        rows = self.booking_service.get_my_bookings(db, student_id=student_id)
        slots = {
            slot.id: slot
            for slot in db.query(ConsultationSlot).filter(
                ConsultationSlot.id.in_([row.slot_id for row in rows]),
            ).all()
        } if rows else {}
        teacher_ids = {slot.teacher_id for slot in slots.values()}
        teachers = {
            teacher.id: teacher
            for teacher in db.query(User).filter(User.id.in_(teacher_ids)).all()
        } if teacher_ids else {}
        booked_counts = {
            slot_id: count
            for slot_id, count in db.query(
                ConsultationParticipant.slot_id,
                func.count(ConsultationParticipant.id),
            ).filter(
                ConsultationParticipant.slot_id.in_(slots),
                    ConsultationParticipant.booking_status == "CONFIRMED",
            ).group_by(ConsultationParticipant.slot_id).all()
        }
        return [
            {
                "id": row.id,
                "slot_id": row.slot_id,
                "student_id": row.student_id,
                "booking_status": row.booking_status,
                "attendance_status": row.attendance_status,
                "booked_at": row.booked_at.isoformat() if row.booked_at else None,
                "start_at": serialize_local(slots[row.slot_id].start_at) if row.slot_id in slots else None,
                "end_at": serialize_local(slots[row.slot_id].end_at) if row.slot_id in slots else None,
                "teacher_name": (
                    f"{teachers[slots[row.slot_id].teacher_id].first_name} "
                    f"{teachers[slots[row.slot_id].teacher_id].last_name or ''}"
                ).strip() if row.slot_id in slots and slots[row.slot_id].teacher_id in teachers else None,
                "price": (
                    consultation_price_for_participants(
                        booked_counts.get(row.slot_id, 0),
                        slots[row.slot_id].capacity,
                    )
                    if row.slot_id in slots else None
                ),
                "currency": slots[row.slot_id].currency if row.slot_id in slots else None,
            }
            for row in rows
        ]

    def cancel_booking(self, db: Session, *, student_id: int, participant_id: int):
        return self.booking_service.cancel_booking(db, student_id=student_id, participant_id=participant_id)

    def create_invitations(self, db: Session, *, ctx, slot_id: int, student_ids: list[int]):
        return self.invitation_service.create_invitations(
            db,
            ctx=ctx,
            slot_id=slot_id,
            student_ids=student_ids,
        )

    def get_student_invitations(self, db: Session, *, student_id: int):
        return self.invitation_service.list_for_student(db, student_id=student_id)

    def get_student_notifications(self, db: Session, *, student_id: int):
        return self.notification_service.list_for_student(db, student_id=student_id)

    def accept_invitation(self, db: Session, *, student_id: int, invitation_id: int):
        return self.invitation_service.accept(db, student_id=student_id, invitation_id=invitation_id)

    def decline_invitation(self, db: Session, *, student_id: int, invitation_id: int):
        return self.invitation_service.decline(db, student_id=student_id, invitation_id=invitation_id)

    def set_attendance_status(self, db: Session, *, ctx, participant_id: int, status: str):
        return self.attendance_service.set_status(
            db,
            ctx=ctx,
            participant_id=participant_id,
            status=status,
        )

    def get_slot_participants(self, db: Session, *, ctx, slot_id: int):
        return self.attendance_service.list_for_slot(db, ctx=ctx, slot_id=slot_id)

    def set_payment_status(self, db: Session, *, ctx, participant_id: int, status: str):
        return self.settlement_service.set_payment_status(
            db,
            ctx=ctx,
            participant_id=participant_id,
            status=status,
        )

    def get_settlement_summary(self, db: Session, *, ctx, slot_id: int):
        return self.settlement_service.get_summary(db, ctx=ctx, slot_id=slot_id)


consultations_facade = ConsultationsFacade()
