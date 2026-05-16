from sqlalchemy.orm import Session, joinedload
from models import User, UserRole
from models import Role, User


class UserRepository:

    def get_by_email(self, db, email: str):
        return db.query(User).filter(User.email == email).options(joinedload(User.roles).joinedload(UserRole.role)).first()

    def create(self, db, data: dict):
        user = User(**data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    
    def get_students(db: Session):
        return (
            db.query(User)
            .join(User.roles)  # join User -> UserRole
            .join(Role)  # join UserRole -> Role
            .filter(Role.name == "student")
            .all()
        )


user_repository = UserRepository()