from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from models.base import Base


class ConsultationAccessMode(str, Enum):
    PUBLIC = "PUBLIC"
    INVITED = "INVITED"


class ConsultationSlotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class ConsultationSlot(Base):
    __tablename__ = "consultation_slots"
    __table_args__ = (
        CheckConstraint("start_at < end_at", name="ck_consultation_slots_time_order"),
        CheckConstraint("capacity BETWEEN 1 AND 4", name="ck_consultation_slots_capacity"),
        Index("ix_consultation_slots_teacher_day", "teacher_id", "day_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("consultation_days.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, nullable=False, default=4)
    price = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="RUB")
    access_mode = Column(String(16), nullable=False, default=ConsultationAccessMode.PUBLIC.value)
    status = Column(String(16), nullable=False, default=ConsultationSlotStatus.ACTIVE.value)
    booking_open_at = Column(DateTime(timezone=True), nullable=True)
    booking_close_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    generated_by_window = Column(Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self) -> str:
        return f"ConsultationSlot(id={self.id}, teacher_id={self.teacher_id}, start_at={self.start_at}, end_at={self.end_at})"
