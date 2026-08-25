"""Bootstrap the current schema for a clean development database."""

from db.database import SessionLocal, engine
from core.config import settings
from core.security import hash_password
from models import all_models  # noqa: F401
from models.base import Base
from models.domains.auth import Role, User, UserRole


SUPPORTED_ROLES = ("student", "admin", "teacher", "secretary")


def init_db() -> None:
    """Create the schema, roles, and the configured first administrator."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal.begin() as db:
        existing_roles = {role.name for role in db.query(Role).all()}
        for role_name in SUPPORTED_ROLES:
            if role_name not in existing_roles:
                db.add(Role(name=role_name))
        db.flush()

        if not settings.admin_email or not settings.admin_password:
            raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD are required to bootstrap the first administrator")

        admin_role = db.query(Role).filter(Role.name == "admin").one()
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if admin:
            has_admin_role = any(user_role.role_id == admin_role.id for user_role in admin.roles)
            if not has_admin_role:
                raise RuntimeError(f"Configured ADMIN_EMAIL belongs to a non-admin user: {settings.admin_email}")
            return

        admin = User(
            email=settings.admin_email,
            first_name="Admin",
            middle_name="Admin",
            password_hash=hash_password(settings.admin_password),
        )
        db.add(admin)
        db.flush()
        db.add(UserRole(user_id=admin.id, role_id=admin_role.id))


if __name__ == "__main__":
    init_db()
