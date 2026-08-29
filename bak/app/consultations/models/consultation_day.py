from __future__ import annotations

from datetime import date, time
from enum import Enum

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


class ConsultationDayStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ConsultationDay(Base):
    __tablename__ = "consultation_days"
    __table_args__ = (
        UniqueConstraint("date", name="uq_consultation_days_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(16), nullable=False, default=ConsultationDayStatus.OPEN.value)
    available_from = Column(Time, nullable=True)
    available_to = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    teacher = relationship("User")

    def __repr__(self) -> str:
        return f"ConsultationDay(id={self.id}, date={self.date}, status={self.status})"
