from datetime import datetime

from pydantic import BaseModel


class AchievementCreate(BaseModel):
    title: str
    description: str | None = None
    event_date: datetime | None = None
    certificate_url: str | None = None


class AssignAchievement(BaseModel):
    user_id: int
    achievement_id: int


class AchievementResponse(BaseModel):
    id: int
    title: str
    description: str | None
    event_date: datetime | None
    certificate_url: str | None

    class Config:
        from_attributes = True
