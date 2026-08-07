from sqlalchemy.orm import Session

from models.domains.auth import User
from models.domains.education import Group, GroupEnrollment, GroupMember


class AdminRepository:
    def get_user_by_id(self, db: Session, *, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def create_group_member(self, db: Session, member: GroupMember) -> GroupMember:
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    def create_enrollment(self, db: Session, enrollment: GroupEnrollment) -> GroupEnrollment:
        db.add(enrollment)
        db.flush()
        db.refresh(enrollment)
        return enrollment


admin_repository = AdminRepository()
