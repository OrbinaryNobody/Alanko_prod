from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class GroupCreatedEvent(DomainEvent):
    group_id: int
    created_by: int


@dataclass(frozen=True)
class StudentEnrolledEvent(DomainEvent):
    enrollment_id: int
    group_id: int
    student_id: int


@dataclass(frozen=True)
class StudentScoreUpdatedEvent(DomainEvent):
    student_task_id: int
    student_id: int
    score: int | None
