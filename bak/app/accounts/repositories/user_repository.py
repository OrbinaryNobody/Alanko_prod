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


user_repository = UserRepository()
