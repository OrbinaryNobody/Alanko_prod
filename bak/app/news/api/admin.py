from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import ConflictError, DomainError, to_http_exception
from core.permissions import require_manage_news
from db.database import get_db
from news.dtos import NewsListResponse
from news.facade import news_facade
from news.schemas import NewsCreate, NewsStatus, NewsUpdate


router = APIRouter(prefix="/admin/news", tags=["admin-news"])


def _status(value: str | None) -> NewsStatus | None:
    if not value:
        return None
    try:
        return NewsStatus(value)
    except ValueError as exc:
        raise ConflictError("Invalid news status") from exc


@router.get("", response_model=NewsListResponse)
def list_news(ctx: AccessContext = Depends(require_manage_news), db: Session = Depends(get_db)):
    return {"items": news_facade.list_admin(db, ctx)}


@router.post("", status_code=201)
async def create_news(
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form("draft"),
    image: UploadFile = File(...),
    ctx: AccessContext = Depends(require_manage_news),
    db: Session = Depends(get_db),
):
    try:
        return await news_facade.create(db, ctx, NewsCreate(title=title, description=description, status=_status(status)), image)
    except DomainError as exc:
        to_http_exception(exc)


@router.patch("/{news_id}")
async def update_news(
    news_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    status: str | None = Form(None),
    image: UploadFile | None = File(None),
    ctx: AccessContext = Depends(require_manage_news),
    db: Session = Depends(get_db),
):
    try:
        data = NewsUpdate(title=title, description=description, status=_status(status))
        return await news_facade.update(db, ctx, news_id, data, image)
    except DomainError as exc:
        to_http_exception(exc)


@router.delete("/{news_id}", status_code=204)
def delete_news(news_id: int, ctx: AccessContext = Depends(require_manage_news), db: Session = Depends(get_db)):
    try:
        news_facade.archive(db, ctx, news_id)
    except DomainError as exc:
        to_http_exception(exc)
