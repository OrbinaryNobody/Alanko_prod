from sqlalchemy.orm import Session

from models.domains.news import News


class NewsRepository:
    def list_all(self, db: Session, *, limit: int = 50, offset: int = 0) -> list[News]:
        return db.query(News).order_by(News.created_at.desc(), News.id.desc()).offset(offset).limit(limit).all()

    def list_published(self, db: Session, *, limit: int = 20, offset: int = 0) -> list[News]:
        return (
            db.query(News)
            .filter(News.status == "published")
            .order_by(News.published_at.desc(), News.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id(self, db: Session, news_id: int) -> News | None:
        return db.query(News).filter(News.id == news_id).first()


news_repository = NewsRepository()
