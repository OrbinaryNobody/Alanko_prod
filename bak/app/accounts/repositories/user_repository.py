from sqlalchemy.orm import Session, joinedload

from models.domains.auth import Role, User, UserRole


class UserRepository:
    def get_by_email(self, db: Session, email: str):
        return (
            db.query(User)
            .filter(User.email == email)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .first()
        )

    def get_by_id(self, db: Session, user_id: int):
        return (
            db.query(User)
            .filter(User.id == user_id)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .first()
        )

    def create(self, db: Session, data: dict):
        user = User(**data)
        db.add(user)
        db.flush()
        db.refresh(user)
        return user

    def get_students(self, db: Session):
        return (
            db.query(User)
            .join(User.roles)
            .join(Role)
            .filter(Role.name == "student")
            .all()
        )

    def list_users(self, db: Session, *, role: str | None = None):
        query = db.query(User).options(joinedload(User.roles).joinedload(UserRole.role))
        if role:
            query = query.join(User.roles).join(Role).filter(Role.name == role)
        return query.order_by(User.last_name, User.first_name, User.id).all()


user_repository = UserRepository()
