from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from db.minio_client import BUCKET_NAMES
from infrastructure.storage.file_service import file_service
from models.domains.news import News
from news.dtos import NewsResponse
from news.repositories import news_repository
from news.schemas import NewsCreate, NewsStatus, NewsUpdate


class NewsService:
    def _require_manage(self, ctx: AccessContext) -> None:
        if not ctx.is_admin and not ctx.can("manage_news"):
            raise PermissionDenied("Access denied to manage news")

    def _to_response(self, item: News) -> NewsResponse:
        return NewsResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            image_url=(file_service.get_file_url(item.image_key, BUCKET_NAMES["news"]) if item.image_key else None),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at,
            published_at=item.published_at,
        )

    def list_admin(self, db: Session, ctx: AccessContext) -> list[NewsResponse]:
        self._require_manage(ctx)
        return [self._to_response(item) for item in news_repository.list_all(db)]

    def list_public(self, db: Session, *, limit: int = 20, offset: int = 0) -> list[NewsResponse]:
        return [self._to_response(item) for item in news_repository.list_published(db, limit=limit, offset=offset)]

    async def create(self, db: Session, ctx: AccessContext, data: NewsCreate, image) -> NewsResponse:
        self._require_manage(ctx)
        if image is None:
            raise ConflictError("News image is required")
        image_key = await self._upload_image(image)
        now = datetime.now(timezone.utc) if data.status == NewsStatus.PUBLISHED else None
        item = News(
            title=data.title.strip(),
            description=data.description.strip(),
            image_key=image_key,
            status=data.status.value,
            created_by=ctx.user_id,
            published_at=now,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return self._to_response(item)

    async def update(self, db: Session, ctx: AccessContext, news_id: int, data: NewsUpdate, image) -> NewsResponse:
        self._require_manage(ctx)
        item = news_repository.get_by_id(db, news_id)
        if not item:
            raise NotFoundError("News not found")

        old_image_key = item.image_key
        if data.title is not None:
            item.title = data.title.strip()
        if data.description is not None:
            item.description = data.description.strip()
        if data.status is not None:
            item.status = data.status.value
            item.published_at = datetime.now(timezone.utc) if data.status == NewsStatus.PUBLISHED else None
        if image:
            item.image_key = await self._upload_image(image)
        item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)

        if image and old_image_key:
            file_service.delete_file(old_image_key, BUCKET_NAMES["news"])
        return self._to_response(item)

    def archive(self, db: Session, ctx: AccessContext, news_id: int) -> None:
        self._require_manage(ctx)
        item = news_repository.get_by_id(db, news_id)
        if not item:
            raise NotFoundError("News not found")
        item.status = NewsStatus.ARCHIVED.value
        item.updated_at = datetime.now(timezone.utc)
        db.commit()

    async def _upload_image(self, image) -> str:
        if image.content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            raise ConflictError("Invalid news image type")
        return await file_service.upload_news_image(image)


news_service = NewsService()
