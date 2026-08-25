from sqlalchemy.orm import Session

from core.access import AccessContext
from news.schemas import NewsCreate, NewsUpdate
from news.services import news_service


class NewsFacade:
    def list_admin(self, db: Session, ctx: AccessContext):
        return news_service.list_admin(db, ctx)

    def list_public(self, db: Session, *, limit: int = 20, offset: int = 0):
        return news_service.list_public(db, limit=limit, offset=offset)

    async def create(self, db: Session, ctx: AccessContext, data: NewsCreate, image):
        return await news_service.create(db, ctx, data, image)

    async def update(self, db: Session, ctx: AccessContext, news_id: int, data: NewsUpdate, image):
        return await news_service.update(db, ctx, news_id, data, image)

    def archive(self, db: Session, ctx: AccessContext, news_id: int):
        return news_service.archive(db, ctx, news_id)


news_facade = NewsFacade()
