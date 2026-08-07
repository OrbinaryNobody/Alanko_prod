from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgramCreatePayload:
    id: int
    title: str
    status: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "description": self.description,
        }


@dataclass(frozen=True)
class BlockCreatePayload:
    id: int
    title: str
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "order": self.order,
        }


@dataclass(frozen=True)
class GroupCreatePayload:
    id: int
    title: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
        }


@dataclass(frozen=True)
class TaskCreatePayload:
    id: int
    title: str
    max_score: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "max_score": self.max_score,
        }


@dataclass(frozen=True)
class MemberAddPayload:
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
class EnrollmentCreatePayload:
    id: int
    student_id: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
        }


@dataclass(frozen=True)
class UserCreatePayload:
    user_id: int
    email: str
    password: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "password": self.password,
        }
