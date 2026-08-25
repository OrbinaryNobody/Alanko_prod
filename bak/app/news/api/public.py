from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from news.dtos import NewsListResponse
from news.facade import news_facade


router = APIRouter(prefix="/public/news", tags=["public-news"])


@router.get("", response_model=NewsListResponse)
def list_public_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return {"items": news_facade.list_public(db, limit=limit, offset=offset)}
