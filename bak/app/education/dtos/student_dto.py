from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StudentPayload:
    id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    full_name: str | None = None
    image_url: str | None = None
    password: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "full_name": self.full_name,
            "image_url": self.image_url,
            "password": self.password,
        }


@dataclass(frozen=True)
class StudentTaskVideoPayload:
    media_id: int
    video_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "video_url": self.video_url,
        }


@dataclass(frozen=True)
class StudentTaskPayload:
    student_task_id: int
    task_id: int | None
    title: str | None
    description: str | None
    category_name: str | None
    status: str | None
    score: int | None
    max_score: int | None
    has_video: bool
    videos: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_task_id": self.student_task_id,
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "category_name": self.category_name,
            "status": self.status,
            "score": self.score,
            "max_score": self.max_score,
            "has_video": self.has_video,
            "videos": self.videos or [],
        }


@dataclass(frozen=True)
class StudentCategoryPayload:
    category_name: str
    tasks: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category_name": self.category_name,
            "tasks": self.tasks,
        }


@dataclass(frozen=True)
class StudentSummaryPayload:
    student_id: int
    student_name: str | None
    email: str | None
    password: str | None
    rating_points: int | None
    last_rank: int | None
    movement: str
    image_url: str | None
    tasks_count: int
    categories: list[dict[str, Any]]
    rank: int
    rank_delta: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "email": self.email,
            "password": self.password,
            "rating_points": self.rating_points,
            "last_rank": self.last_rank,
            "movement": self.movement,
            "image_url": self.image_url,
            "tasks_count": self.tasks_count,
            "categories": self.categories,
            "rank": self.rank,
            "rank_delta": self.rank_delta,
        }


@dataclass(frozen=True)
class GroupStudentPayload:
    id: int
    student_id: int
    status: str | None
    current_block_id: int | None
    completion_percent: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "status": self.status,
            "current_block_id": self.current_block_id,
            "completion_percent": self.completion_percent,
        }
