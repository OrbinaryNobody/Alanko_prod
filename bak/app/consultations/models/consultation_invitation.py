from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from models.base import Base


class ConsultationInvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


class ConsultationInvitation(Base):
    __tablename__ = "consultation_invitations"
    __table_args__ = (
        Index("ix_consultation_invitations_slot_student_status", "slot_id", "student_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("consultation_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(16), nullable=False, default=ConsultationInvitationStatus.PENDING.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
