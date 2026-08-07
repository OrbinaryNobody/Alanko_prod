from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AchievementPayload:
    id: int
    title: str
    description: str | None
    event_date: str | None
    place: str | None
    is_collective: bool
    file_url: str | None = None
    video_url: str | None = None
    awarded_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_date": self.event_date,
            "place": self.place,
            "is_collective": self.is_collective,
            "file_url": self.file_url,
            "video_url": self.video_url,
            "awarded_at": self.awarded_at,
        }


@dataclass(frozen=True)
class AchievementCreateResponse:
    achievement_id: int
    message: str
    student_id: int | None = None
    file_id: str | None = None
    file_url: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AchievementCreateResponse":
        return cls(
            achievement_id=payload.get("achievement_id"),
            message=payload.get("message", "achievement created"),
            student_id=payload.get("student_id"),
            file_id=payload.get("file_id"),
            file_url=payload.get("file_url"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "message": self.message,
            "achievement_id": self.achievement_id,
            "student_id": self.student_id,
        }
        if self.file_id is not None:
            result["file_id"] = self.file_id
        if self.file_url is not None:
            result["file_url"] = self.file_url
        return result


@dataclass(frozen=True)
class AchievementUploadResponse:
    message: str
    achievement_id: int
    file_url: str | None = None
    video_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "message": self.message,
            "achievement_id": self.achievement_id,
        }
        if self.file_url is not None:
            result["file_url"] = self.file_url
        if self.video_url is not None:
            result["video_url"] = self.video_url
        return result


@dataclass(frozen=True)
class AchievementAssignmentResponse:
    achievement_id: int
    user_id: int
    assigned_by: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": "assigned",
            "achievement_id": self.achievement_id,
            "user_id": self.user_id,
            "assigned_by": self.assigned_by,
        }
