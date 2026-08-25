from pydantic import BaseModel


class AttendanceHistoryItemResponse(BaseModel):
    id: int
    student_id: int
    group_id: int | None = None
    attendance_date: str
    checked_in_at: str | None = None
    status: str
    marked_by: int | None = None
    comment: str | None = None


class AttendanceHistoryResponse(BaseModel):
    student_id: int
    items: list[AttendanceHistoryItemResponse]