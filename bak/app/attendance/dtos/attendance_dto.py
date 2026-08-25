from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AttendancePayload:
    id: int
    student_id: int
    group_id: int | None
    attendance_date: str
    checked_in_at: str | None
    status: str
    marked_by: int | None
    comment: str | None
    subscription_remaining_visits: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "group_id": self.group_id,
            "attendance_date": self.attendance_date,
            "checked_in_at": self.checked_in_at,
            "status": self.status,
            "marked_by": self.marked_by,
            "comment": self.comment,
            "subscription_remaining_visits": self.subscription_remaining_visits,
        }


@dataclass(frozen=True)
class AttendanceSummaryPayload:
    date: str
    checked_count: int
    total_students: int
    active_subscriptions: int
    warning_subscriptions: int
    debt_count: int

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()