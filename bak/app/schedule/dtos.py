from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CalendarEventPayload:
    id: str
    type: str
    title: str
    start_at: datetime
    end_at: datetime
    status: str
    color: str
    teacher_id: int
    day_id: int | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["start_at"] = self.start_at.isoformat()
        payload["end_at"] = self.end_at.isoformat()
        return payload
