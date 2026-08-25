from datetime import date

from pydantic import BaseModel, Field


class AttendanceCheckInCreate(BaseModel):
    student_id: int
    group_id: int | None = None
    attendance_date: date
    comment: str | None = Field(default=None, max_length=1000)


class SubscriptionCreate(BaseModel):
    plan_name: str = Field(min_length=1, max_length=128)
    total_visits: int = Field(gt=0)
    valid_from: date
    valid_until: date
    payment_status: str = Field(default="UNPAID", pattern=r"^(PAID|UNPAID|PARTIAL|REFUNDED)$")
    amount: int = Field(default=0, ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=8)