from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardPayload:
    user_id: int
    rating: int
    tasks: int
    place: int | None
    total_students: int
    history: list[dict[str, Any]] | None = None
    leaderboard: list[dict[str, Any]] | None = None
    leaderboards: dict[str, Any] | None = None
    leaderboard_totals: dict[str, int] | None = None
    videos: list[dict[str, Any]] | None = None
    achievement_videos: list[dict[str, Any]] | None = None
    achievements: dict[str, Any] | None = None
    user: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "rating": self.rating,
            "tasks": self.tasks,
            "place": self.place,
            "total_students": self.total_students,
            "history": self.history or [],
            "leaderboard": self.leaderboard or [],
            "leaderboards": self.leaderboards or {"group": [], "overall": []},
            "leaderboard_totals": self.leaderboard_totals or {"group": 0, "overall": 0},
            "videos": self.videos or [],
            "achievement_videos": self.achievement_videos or [],
            "achievements": self.achievements or {"individual": [], "collective": []},
            "user": self.user or {},
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
