from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func

from models.base import Base


class SpecialOffer(Base):
    __tablename__ = "special_offers"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    price = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="RUB")
    status = Column(String(32), nullable=False, default="DRAFT")
    registration_opens_at = Column(TIMESTAMP(timezone=True))
    registration_closes_at = Column(TIMESTAMP(timezone=True))
    starts_at = Column(TIMESTAMP(timezone=True))
    ends_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("user_id", "special_offer_id", "status", name="uq_payments_user_offer_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    special_offer_id = Column(Integer, ForeignKey("special_offers.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(64), nullable=False, default="YOOKASSA")
    provider_payment_id = Column(String(255), unique=True, nullable=True, index=True)
    amount = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="RUB")
    status = Column(String(32), nullable=False, default="PENDING")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(TIMESTAMP(timezone=True))


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_course_enrollment_user_course"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="PENDING")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    activated_at = Column(TIMESTAMP(timezone=True))
