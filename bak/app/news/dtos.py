from datetime import datetime

from pydantic import BaseModel


class NewsResponse(BaseModel):
    id: int
    title: str
    description: str
    image_url: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None
    published_at: datetime | None


class NewsListResponse(BaseModel):
    items: list[NewsResponse]
