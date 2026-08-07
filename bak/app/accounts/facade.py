from sqlalchemy.orm import Session

from accounts.services.auth_service import auth_service

# Public contract for the accounts context. Other contexts should use this facade
# instead of importing accounts services directly.


class AccountsFacade:
    def add_user_by_admin(self, db: Session, *, data):
        return auth_service.add_user_by_admin(db, data=data)

    def add_student_by_teacher(self, db: Session, *, data, image_url: str):
        return auth_service.add_student_by_teacher(db, data=data, image_url=image_url)


accounts_facade = AccountsFacade()
