from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgramPayload:
    id: int
    title: str
    description: str | None
    status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
        }


@dataclass(frozen=True)
class BlockPayload:
    id: int
    title: str
    order: int
    status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "order": self.order,
            "status": self.status,
        }


@dataclass(frozen=True)
class GroupPayload:
    id: int
    title: str
    program_id: int | None = None
    status: str | None = None
    leaderboard_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "program_id": self.program_id,
            "status": self.status,
            "leaderboard_enabled": self.leaderboard_enabled,
        }


@dataclass(frozen=True)
class GroupMemberPayload:
    group_id: int
    user_id: int
    role: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role,
        }


@dataclass(frozen=True)
class StudentEnrollmentPayload:
    id: int
    student_id: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
        }


@dataclass(frozen=True)
class TaskPayload:
    id: int
    title: str
    description: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    difficulty: str | None = None
    max_score: int | None = None
    deadline: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "difficulty": self.difficulty,
            "max_score": self.max_score,
            "deadline": self.deadline,
        }


@dataclass(frozen=True)
class StudentTaskUploadPayload:
    media_id: int
    student_id: int
    student_task_id: int
    video_id: str
    video_url: str
    status: str | None = None
    has_video: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": "video uploaded",
            "media_id": self.media_id,
            "student_id": self.student_id,
            "student_task_id": self.student_task_id,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "status": self.status,
            "has_video": self.has_video,
        }


@dataclass(frozen=True)
class StudentTaskUpdatePayload:
    student_task_id: int
    status: str | None = None
    score: int | None = None
    comment: str | None = None
    max_score: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_task_id": self.student_task_id,
            "status": self.status,
            "score": self.score,
            "comment": self.comment,
            "max_score": self.max_score,
        }
