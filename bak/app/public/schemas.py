from pydantic import BaseModel


class PublicAchievementVideoResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    video_url: str
    event_date: str | None = None


class PublicAchievementVideosResponse(BaseModel):
    items: list[PublicAchievementVideoResponse]