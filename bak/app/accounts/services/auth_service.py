import secrets
import string

from sqlalchemy.orm import Session

from core.exceptions import ConflictError, PermissionDenied
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
                db.add(StudentProfile(user_id=user.id))

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
            db.add(StudentProfile(user_id=user.id, image_url=image_url))

            return user, generated_password

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
            ]

        if role == "student":
            return [
                Permission.VIEW_OWN_DASHBOARD,
                Permission.VIEW_OWN_TASKS,
                Permission.VIEW_OWN_ACHIEVEMENTS,
                Permission.VIEW_ASSESSMENT,
            ]

        return []


auth_service = AuthService()
