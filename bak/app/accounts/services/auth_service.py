import secrets
import string

from sqlalchemy.orm import Session

from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from core.permissions import Permission
from core.security import create_access_token, hash_password, verify_password
from models.domains.auth import Role, UserRole
from models.domains.student import StudentProfile, TaskMedia
from models.domains.education import GroupEnrollment, GroupMember, GroupSchedule
from models.domains.attendance import ParentGuardian, StudentParent
from accounts.repositories.user_repository import user_repository
from shared.unit_of_work import UnitOfWork
from db.minio_client import BUCKET_NAMES
from infrastructure.storage.file_service import file_service


class AuthService:
    def _generate_random_password(self, length: int = 12) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(characters) for _ in range(length))
        return password

    def add_user_by_admin(self, db: Session, *, data, image_url: str | None = None) -> tuple[object, str]:
        existing_user = user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ConflictError("Email already registered")

        role = db.query(Role).filter(Role.name == data.role).first()
        if not role:
            raise ConflictError(f"Role '{data.role}' not found")

        generated_password = data.password or self._generate_random_password()
        hashed_password = hash_password(generated_password)

        with UnitOfWork(db):
            user = user_repository.create(db, {
                "email": data.email,
                "password_hash": hashed_password,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "middle_name": data.middle_name,
                "image_url": image_url,
            })

            db.add(UserRole(user_id=user.id, role_id=role.id))

            if data.role == "student":
                db.add(StudentProfile(user_id=user.id, birth_year=getattr(data, "birth_year", None)))

            return user, generated_password

    def list_users(self, db: Session, *, role: str | None = None) -> list[dict]:
        users = user_repository.list_users(db, role=role)
        return [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "middle_name": user.middle_name,
                "full_name": " ".join(part for part in (user.first_name, user.last_name) if part),
                "roles": [user_role.role.name for user_role in user.roles if user_role.role],
                "avatar_url": file_service.get_file_url(user.image_url, BUCKET_NAMES["student_photos"]) if user.image_url else None,
            }
            for user in users
        ]

    def add_student_by_teacher(
        self,
        db: Session,
        *,
        data,
        image_url: str,
        parent: dict | None = None,
    ):
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
                "first_name": data.first_name,
                "last_name": data.last_name,
                "middle_name": data.middle_name,
            })

            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.add(StudentProfile(user_id=user.id, image_url=image_url, birth_year=getattr(data, "birth_year", None)))
            if parent:
                parent_record = ParentGuardian(**parent)
                db.add(parent_record)
                db.flush()
                db.add(StudentParent(student_id=user.id, parent_id=parent_record.id, is_primary=1))

            return user

    def is_student(self, db: Session, *, user_id: int) -> bool:
        user = user_repository.get_by_id(db, user_id)
        return bool(user and any(user_role.role and user_role.role.name == "student" for user_role in user.roles))

    def _is_teacher(self, user) -> bool:
        return bool(user and any(item.role and item.role.name == "teacher" for item in user.roles))

    def get_teacher_details(self, db: Session, *, teacher_id: int):
        user = user_repository.get_by_id(db, teacher_id)
        if not self._is_teacher(user):
            raise NotFoundError("Teacher not found")
        groups = db.query(GroupMember).filter(
            GroupMember.user_id == teacher_id,
            GroupMember.role == "teacher",
        ).all()
        group_items = [{"id": member.group.id, "title": member.group.title} for member in groups]
        student_count = sum(
            len(member.group.enrollments)
            for member in groups
        )
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "avatar_url": file_service.get_file_url(user.image_url, BUCKET_NAMES["student_photos"]) if user.image_url else None,
            "groups": group_items,
            "group_count": len(group_items),
            "student_count": student_count,
        }

    def update_teacher(self, db: Session, *, teacher_id: int, data):
        user = user_repository.get_by_id(db, teacher_id)
        if not self._is_teacher(user):
            raise NotFoundError("Teacher not found")
        if data.email is not None and data.email != user.email:
            existing = user_repository.get_by_email(db, data.email)
            if existing and existing.id != teacher_id:
                raise ConflictError("Email already registered")
            user.email = data.email
        for field in ("first_name", "last_name", "middle_name"):
            value = getattr(data, field)
            if value is not None:
                setattr(user, field, value)
        with UnitOfWork(db):
            db.flush()
            db.refresh(user)
        return self.get_teacher_details(db, teacher_id=teacher_id)

    def update_teacher_photo(self, db: Session, *, teacher_id: int, image_url: str):
        user = user_repository.get_by_id(db, teacher_id)
        if not self._is_teacher(user):
            raise NotFoundError("Teacher not found")
        old_image_url = user.image_url
        with UnitOfWork(db):
            user.image_url = image_url
            db.flush()
            db.refresh(user)
        if old_image_url and old_image_url != "default.jpg":
            file_service.delete_file(old_image_url, BUCKET_NAMES["student_photos"])
        return self.get_teacher_details(db, teacher_id=teacher_id)

    def reset_teacher_password(self, db: Session, *, teacher_id: int):
        user = user_repository.get_by_id(db, teacher_id)
        if not self._is_teacher(user):
            raise NotFoundError("Teacher not found")
        generated_password = self._generate_random_password()
        with UnitOfWork(db):
            user.password_hash = hash_password(generated_password)
            db.flush()
        return generated_password

    def delete_teacher(self, db: Session, *, teacher_id: int):
        user = user_repository.get_by_id(db, teacher_id)
        if not self._is_teacher(user):
            raise NotFoundError("Teacher not found")
        old_image_url = user.image_url
        with UnitOfWork(db):
            db.query(GroupSchedule).filter(GroupSchedule.teacher_id == teacher_id).delete(synchronize_session=False)
            db.query(GroupMember).filter(GroupMember.user_id == teacher_id).delete(synchronize_session=False)
            db.query(TaskMedia).filter(TaskMedia.uploaded_by == teacher_id).delete(synchronize_session=False)
            for user_role in list(user.roles):
                db.delete(user_role)
            db.delete(user)
        if old_image_url:
            file_service.delete_file(old_image_url, BUCKET_NAMES["student_photos"])
        return teacher_id

    def delete_student(self, db: Session, *, student_id: int):
        user = user_repository.get_by_id(db, student_id)
        if not user:
            raise NotFoundError("Student not found")

        has_student_role = any(role.role.name == "student" for role in user.roles)
        if not has_student_role:
            raise NotFoundError("Student not found")

        with UnitOfWork(db):
            for user_role in list(user.roles):
                db.delete(user_role)
            db.delete(user)
        return user

    def get_student_details(self, db: Session, *, student_id: int):
        user = user_repository.get_by_id(db, student_id)
        if not user or not any(role.role and role.role.name == "student" for role in user.roles):
            raise NotFoundError("Student not found")
        profile = user.student_profile
        enrollments = db.query(GroupEnrollment).filter(
            GroupEnrollment.student_id == user.id,
            GroupEnrollment.status == "active",
        ).all()
        program_points = sum(task.grade or 0 for enrollment in enrollments for task in enrollment.tasks)
        total_tasks = sum(len(enrollment.tasks) for enrollment in enrollments)
        completed_tasks = sum(
            1 for enrollment in enrollments for task in enrollment.tasks
            if task.grade is not None or task.status == "completed"
        )
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "birth_year": profile.birth_year if profile else None,
            "image_url": file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"]) if profile and profile.image_url else None,
            "rating_points": program_points,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "groups": [{"id": enrollment.group.id, "title": enrollment.group.title} for enrollment in enrollments],
        }

    def update_student_photo(self, db: Session, *, student_id: int, image_url: str):
        user = user_repository.get_by_id(db, student_id)
        if not user or not any(role.role and role.role.name == "student" for role in user.roles):
            raise NotFoundError("Student not found")
        if user.student_profile is None:
            user.student_profile = StudentProfile(user_id=user.id)
            db.add(user.student_profile)
        old_image_url = user.student_profile.image_url
        with UnitOfWork(db):
            user.student_profile.image_url = image_url
            db.flush()
            db.refresh(user.student_profile)
        if old_image_url and old_image_url != "default.jpg":
            file_service.delete_file(old_image_url, BUCKET_NAMES["student_photos"])
        return self.get_student_details(db, student_id=student_id)

    def reset_student_password(self, db: Session, *, student_id: int):
        user = user_repository.get_by_id(db, student_id)
        if not user or not any(role.role and role.role.name == "student" for role in user.roles):
            raise NotFoundError("Student not found")
        generated_password = self._generate_random_password()
        with UnitOfWork(db):
            user.password_hash = hash_password(generated_password)
            db.flush()
        return generated_password

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
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
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
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
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

        if role == "secretary":
            return [
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
            ]

        return []


auth_service = AuthService()
