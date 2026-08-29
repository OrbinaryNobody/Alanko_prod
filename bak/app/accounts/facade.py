from sqlalchemy.orm import Session

from accounts.services.auth_service import auth_service

# Public contract for the accounts context. Other contexts should use this facade
# instead of importing accounts services directly.


class AccountsFacade:
    def list_users(self, db: Session, *, role: str | None = None):
        return auth_service.list_users(db, role=role)

    def add_user_by_admin(self, db: Session, *, data, image_url: str | None = None):
        return auth_service.add_user_by_admin(db, data=data, image_url=image_url)

    def add_student_by_teacher(self, db: Session, *, data, image_url: str, parent: dict | None = None):
        return auth_service.add_student_by_teacher(db, data=data, image_url=image_url, parent=parent)

    def is_student(self, db: Session, *, user_id: int) -> bool:
        return auth_service.is_student(db, user_id=user_id)

    def delete_student(self, db: Session, *, student_id: int):
        return auth_service.delete_student(db, student_id=student_id)

    def get_student_details(self, db: Session, *, student_id: int):
        return auth_service.get_student_details(db, student_id=student_id)

    def update_student_photo(self, db: Session, *, student_id: int, image_url: str):
        return auth_service.update_student_photo(db, student_id=student_id, image_url=image_url)

    def reset_student_password(self, db: Session, *, student_id: int):
        return auth_service.reset_student_password(db, student_id=student_id)

    def update_student(self, db: Session, *, student_id: int, data):
        return auth_service.update_student(db, student_id=student_id, data=data)

    def get_teacher_details(self, db: Session, *, teacher_id: int):
        return auth_service.get_teacher_details(db, teacher_id=teacher_id)

    def update_teacher(self, db: Session, *, teacher_id: int, data):
        return auth_service.update_teacher(db, teacher_id=teacher_id, data=data)

    def update_teacher_photo(self, db: Session, *, teacher_id: int, image_url: str):
        return auth_service.update_teacher_photo(db, teacher_id=teacher_id, image_url=image_url)

    def reset_teacher_password(self, db: Session, *, teacher_id: int):
        return auth_service.reset_teacher_password(db, teacher_id=teacher_id)

    def delete_teacher(self, db: Session, *, teacher_id: int):
        return auth_service.delete_teacher(db, teacher_id=teacher_id)


accounts_facade = AccountsFacade()
