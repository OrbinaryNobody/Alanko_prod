from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InvitationPayload:
    id: int
    slot_id: int
    student_id: int
    status: str
    created_at: datetime | None = None
    responded_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for field in ("created_at", "responded_at"):
            if payload[field] is not None:
                payload[field] = payload[field].isoformat()
        return payload


@dataclass(frozen=True)
class NotificationPayload:
    id: int
    notification_type: str
    title: str
    body: str
    invitation_id: int | None
    read_at: datetime | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for field in ("read_at", "created_at"):
            if payload[field] is not None:
                payload[field] = payload[field].isoformat()
        return payload


@dataclass(frozen=True)
class ParticipantPayload:
    id: int
    slot_id: int
    student_id: int
    booking_status: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AttendancePayload:
    id: int
    slot_id: int
    student_id: int
    booking_status: str
    attendance_status: str
    payment_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
