from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class ConsultationNotification(Base):
    __tablename__ = "consultation_notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invitation_id = Column(Integer, ForeignKey("consultation_invitations.id", ondelete="CASCADE"), nullable=True, index=True)
    notification_type = Column(String(32), nullable=False, default="CONSULTATION_INVITATION")
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
