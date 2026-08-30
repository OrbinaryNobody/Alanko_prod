from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    difficulty: int = 1
    max_score: int = 100


class TaskUpdate(BaseModel):
    title: str
    description: str | None = None
    difficulty: int = 1
    max_score: int = 100


class StudentTaskUpdate(BaseModel):
    status: str | None = None
    score: int | None = None
    comment: str | None = None
