import secrets
import string
from repositories.user_repository import user_repository
from core.security import hash_password, verify_password, create_access_token
from models import UserRole, Role, StudentProfile


class AuthService:

    def _generate_random_password(self, length: int = 12) -> str:
        """Генерирует случайный пароль"""
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password

    def add_user_by_admin(self, db, data):
        existing_user = user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Проверяем, что роль существует
        role = db.query(Role).filter(Role.name == data.role).first()
        if not role:
            raise ValueError(f"Role '{data.role}' not found")

        hashed_password = hash_password(data.password)

        user = user_repository.create(db, {
            "email": data.email,
            "password_hash": hashed_password,
            "plain_password": data.password,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "middle_name": data.middle_name
        })

        # Присваиваем роль
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)

        # Если роль "student", создаём профиль
        if data.role == "student":
            student_profile = StudentProfile(user_id=user.id)
            db.add(student_profile)

        db.commit()

        return user

    def add_student_by_teacher(self, db, data, image_url: str):
        """Добавляет студента учителем с автогенерацией пароля и фото"""
        existing_user = user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Проверяем, что роль "student" существует
        role = db.query(Role).filter(Role.name == "student").first()
        if not role:
            raise ValueError("Role 'student' not found")

        # Генерируем случайный пароль
        generated_password = self._generate_random_password()
        hashed_password = hash_password(generated_password)

        user = user_repository.create(db, {
            "email": data.email,
            "password_hash": hashed_password,
            "plain_password": generated_password,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "middle_name": data.middle_name
        })

        # Присваиваем роль "student"
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)

        # Создаём профиль студента с фото
        student_profile = StudentProfile(user_id=user.id, image_url=image_url)
        db.add(student_profile)

        db.commit()

        return user, generated_password

    def login(self, db, data):
        user = user_repository.get_by_email(db, data.email)

        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Получаем роль пользователя (предполагаем одну роль)
        role = user.roles[0].role.name if user.roles else None

        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": role
        })

        return token


auth_service = AuthService()