from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field


class ConsultationDayCreate(BaseModel):
    date: date
    status: str = "OPEN"
    available_from: time | None = None
    available_to: time | None = None


class ConsultationDayStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(OPEN|CLOSED)$")


class ConsultationSlotCreate(BaseModel):
    day_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    start_at: datetime
    end_at: datetime
    capacity: int = Field(default=4, ge=1, le=4)
    price: int | None = Field(default=None, ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=8)
    access_mode: str = Field(default="PUBLIC", pattern=r"^(PUBLIC|INVITED)$")


class ConsultationInvitationCreate(BaseModel):
    student_ids: list[int] = Field(..., min_length=1)


class ConsultationAttendanceUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(PRESENT|ABSENT)$")


class ConsultationPaymentUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(PAID|UNPAID)$")
