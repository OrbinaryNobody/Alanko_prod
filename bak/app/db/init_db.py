"""Bootstrap the current schema for a clean development database."""

from db.database import SessionLocal, engine
from models import all_models  # noqa: F401
from models.base import Base
from models.domains.auth import Role


SUPPORTED_ROLES = ("student", "admin", "teacher", "secretary")


def init_db() -> None:
    """Create all model-defined tables and ensure the supported roles exist."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal.begin() as db:
        existing_roles = {role.name for role in db.query(Role).all()}
        for role_name in SUPPORTED_ROLES:
            if role_name not in existing_roles:
                db.add(Role(name=role_name))


if __name__ == "__main__":
    init_db()
