import secrets
import string

from sqlalchemy.orm import Session

from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from core.permissions import Permission
from core.security import create_access_token, hash_password, verify_password
from models.domains.auth import Role, UserRole
from models.domains.student import StudentProfile
from repositories.user_repository import user_repository
from shared.unit_of_work import UnitOfWork


class AuthService:
    def _generate_random_password(self, length: int = 12) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(characters) for _ in range(length))
        return password

    def add_user_by_admin(self, db: Session, *, data) -> object:
        existing_user = user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ConflictError("Email already registered")

        role = db.query(Role).filter(Role.name == data.role).first()
        if not role:
            raise ConflictError(f"Role '{data.role}' not found")

        hashed_password = hash_password(data.password)

        with UnitOfWork(db):
            user = user_repository.create(db, {
                "email": data.email,
                "password_hash": hashed_password,
                "plain_password": data.password,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "middle_name": data.middle_name,
            })

            db.add(UserRole(user_id=user.id, role_id=role.id))

            if data.role == "student":
                db.add(StudentProfile(user_id=user.id, birth_year=getattr(data, "birth_year", None)))

            return user

    def add_student_by_teacher(self, db: Session, *, data, image_url: str):
        existing_user = user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ConflictError("Email already registered")

        role = db.query(Role).filter(Role.name == "student").first()
        if not role:
            raise ConflictError("Role 'student' not found")

        generated_password = self._generate_random_password()
        hashed_password = hash_password(generated_password)

        with UnitOfWork(db):
            user = user_repository.create(db, {
                "email": data.email,
                "password_hash": hashed_password,
                "plain_password": generated_password,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "middle_name": data.middle_name,
            })

            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.add(StudentProfile(user_id=user.id, image_url=image_url, birth_year=getattr(data, "birth_year", None)))

            return user, generated_password

    def is_student(self, db: Session, *, user_id: int) -> bool:
        user = user_repository.get_by_id(db, user_id)
        return bool(user and any(user_role.role and user_role.role.name == "student" for user_role in user.roles))

    def delete_student(self, db: Session, *, student_id: int):
        user = user_repository.get_by_id(db, student_id)
        if not user:
            raise NotFoundError("Student not found")

        has_student_role = any(role.role.name == "student" for role in user.roles)
        if not has_student_role:
            raise NotFoundError("Student not found")

        with UnitOfWork(db):
            db.delete(user)
        return user

    def update_student(self, db: Session, *, student_id: int, data):
        user = user_repository.get_by_id(db, student_id)
        if not user:
            raise NotFoundError("Student not found")

        has_student_role = any(role.role.name == "student" for role in user.roles)
        if not has_student_role:
            raise NotFoundError("Student not found")

        if data.email is not None and data.email != user.email:
            existing_user = user_repository.get_by_email(db, data.email)
            if existing_user and existing_user.id != student_id:
                raise ConflictError("Email already registered")
            user.email = data.email

        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.middle_name is not None:
            user.middle_name = data.middle_name

        if user.student_profile is None:
            user.student_profile = StudentProfile(user_id=user.id)
            db.add(user.student_profile)

        if data.birth_year is not None:
            user.student_profile.birth_year = data.birth_year

        with UnitOfWork(db):
            db.flush()
            db.refresh(user)
            if user.student_profile is not None:
                db.refresh(user.student_profile)

        return user

    def login(self, db: Session, *, data) -> str:
        user = user_repository.get_by_email(db, data.email)
        if not user:
            raise PermissionDenied("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise PermissionDenied("Invalid email or password")

        role = user.roles[0].role.name if user.roles else None
        permissions = self._build_permissions(role)
        return create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": role,
            "roles": [role] if role else [],
            "permissions": permissions,
        })

    def _build_permissions(self, role: str | None) -> list[str]:
        if role == "admin":
            return [
                Permission.MANAGE_ACHIEVEMENTS,
                Permission.UPLOAD_MEDIA,
                Permission.VIEW_OWN_DASHBOARD,
                Permission.VIEW_OWN_TASKS,
                Permission.VIEW_OWN_ACHIEVEMENTS,
                Permission.VIEW_ASSESSMENT,
                Permission.VIEW_GROUPS,
                Permission.MANAGE_GROUPS,
                Permission.VIEW_PROGRAMS,
                Permission.CREATE_PROGRAMS,
                Permission.EDIT_PROGRAMS,
                Permission.CREATE_BLOCKS,
                Permission.CREATE_TASKS,
                Permission.GRADE_TASKS,
                Permission.CREATE_MANUAL_TASKS,
                Permission.VIEW_STUDENTS,
                Permission.MANAGE_ENROLLMENTS,
                Permission.VIEW_ACHIEVEMENTS,
                Permission.MANAGE_USERS,
                Permission.VIEW_CONSULTATIONS,
                Permission.BOOK_CONSULTATIONS,
                Permission.MANAGE_CONSULTATIONS,
            ]

        if role == "teacher":
            return [
                Permission.UPLOAD_MEDIA,
                Permission.VIEW_OWN_DASHBOARD,
                Permission.VIEW_OWN_TASKS,
                Permission.VIEW_OWN_ACHIEVEMENTS,
                Permission.VIEW_ASSESSMENT,
                Permission.VIEW_GROUPS,
                Permission.MANAGE_GROUPS,
                Permission.VIEW_PROGRAMS,
                Permission.CREATE_PROGRAMS,
                Permission.EDIT_PROGRAMS,
                Permission.CREATE_BLOCKS,
                Permission.CREATE_TASKS,
                Permission.GRADE_TASKS,
                Permission.CREATE_MANUAL_TASKS,
                Permission.VIEW_STUDENTS,
                Permission.MANAGE_ENROLLMENTS,
                Permission.VIEW_ACHIEVEMENTS,
                Permission.VIEW_CONSULTATIONS,
                Permission.MANAGE_CONSULTATIONS,
            ]

        if role == "student":
            return [
                Permission.VIEW_OWN_DASHBOARD,
                Permission.VIEW_OWN_TASKS,
                Permission.VIEW_OWN_ACHIEVEMENTS,
                Permission.VIEW_ASSESSMENT,
                Permission.VIEW_CONSULTATIONS,
                Permission.BOOK_CONSULTATIONS,
            ]

        return []


auth_service = AuthService()
