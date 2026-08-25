from sqlalchemy import Boolean, Column, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    event_date = Column(TIMESTAMP(timezone=True))
    place = Column(Text)
    is_collective = Column(Boolean, default=False)
    is_public = Column(Boolean, nullable=False, default=True, server_default="true")
    certificate_url = Column(Text)
    video_url = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    users = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))

    awarded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User")
    achievement = relationship("Achievement", back_populates="users")
