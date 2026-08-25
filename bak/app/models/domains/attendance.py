from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


class ParentGuardian(Base):
    __tablename__ = "parent_guardians"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    middle_name = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student_links = relationship("StudentParent", back_populates="parent", cascade="all, delete-orphan")


class StudentParent(Base):
    __tablename__ = "student_parents"
    __table_args__ = (
        UniqueConstraint("student_id", "parent_id", name="uq_student_parent"),
        Index("ix_student_parents_student_primary", "student_id", "is_primary"),
    )

    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("parent_guardians.id", ondelete="CASCADE"), primary_key=True)
    relationship_type = Column(String(32), nullable=False, default="parent")
    is_primary = Column(Integer, nullable=False, default=1)

    student = relationship("User")
    parent = relationship("ParentGuardian", back_populates="student_links")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_student_status", "student_id", "status"),
        Index("ix_subscriptions_valid_until", "valid_until"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name = Column(String(128), nullable=False)
    total_visits = Column(Integer, nullable=False)
    remaining_visits = Column(Integer, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")
    payment_status = Column(String(32), nullable=False, default="UNPAID")
    amount = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="RUB")
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("User")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("student_id", "group_id", "attendance_date", name="uq_attendance_student_group_date"),
        Index("ix_attendance_records_student_date", "student_id", "attendance_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    attendance_date = Column(Date, nullable=False)
    checked_in_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(32), nullable=False, default="PRESENT")
    marked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("User", foreign_keys=[student_id])
    marker = relationship("User", foreign_keys=[marked_by])
    group = relationship("Group")
    subscription = relationship("Subscription")