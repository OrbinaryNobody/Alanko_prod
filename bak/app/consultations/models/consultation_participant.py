from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from models.base import Base


class ConsultationParticipantSource(str, Enum):
    SELF = "SELF"
    INVITATION = "INVITATION"


class ConsultationBookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class ConsultationAttendanceStatus(str, Enum):
    NOT_MARKED = "NOT_MARKED"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


class ConsultationPaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class ConsultationParticipant(Base):
    __tablename__ = "consultation_participants"
    __table_args__ = (
        # Unique by slot + student; cancellation is status change, not record delete.
    )

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("consultation_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(16), nullable=False, default=ConsultationParticipantSource.SELF.value)
    booking_status = Column(String(16), nullable=False, default=ConsultationBookingStatus.CONFIRMED.value)
    attendance_status = Column(String(16), nullable=False, default=ConsultationAttendanceStatus.NOT_MARKED.value)
    payment_status = Column(String(16), nullable=False, default=ConsultationPaymentStatus.UNPAID.value)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    booked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
