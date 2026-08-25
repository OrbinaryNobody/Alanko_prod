from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PublicLeaderboardItem:
    user_id: int
    full_name: str
    rating: int
    image_url: str | None = None
    role: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "rating": self.rating,
            "image_url": self.image_url,
            "role": self.role,
            "description": self.description,
        }


@dataclass(frozen=True)
class PublicLeaderboardPlace:
    place: int
    user_id: int
    full_name: str
    rating: int
    movement: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "place": self.place,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "rating": self.rating,
            "movement": self.movement,
        }


@dataclass(frozen=True)
class PublicLeaderboardPayload:
    top_3_students: list[PublicLeaderboardItem]
    top_5_leaderboard: list[PublicLeaderboardPlace]
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_3_students": [item.to_dict() for item in self.top_3_students],
            "top_5_leaderboard": [item.to_dict() for item in self.top_5_leaderboard],
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PublicStudentVideoItem:
    id: int
    task_name: str
    category: str
    video_url: str
    uploaded_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_name": self.task_name,
            "category": self.category,
            "video_url": self.video_url,
            "uploaded_at": self.uploaded_at,
        }


@dataclass(frozen=True)
class PublicStudentVideosPayload:
    student_id: int
    full_name: str
    videos: list[PublicStudentVideoItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "full_name": self.full_name,
            "videos": [item.to_dict() for item in self.videos],
        }

@dataclass(frozen=True)
class PublicAchievementVideoItem:
    id: int
    title: str
    description: str | None
    video_url: str
    event_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "video_url": self.video_url,
            "event_date": self.event_date,
        }
