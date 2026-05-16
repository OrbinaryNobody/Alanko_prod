from sqlalchemy import (
    Boolean, Column, Integer, Text, TIMESTAMP,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ================================
# Роли
# ================================
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)

    users = relationship("UserRole", back_populates="role")


# ================================
# Пользователи
# ================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text)
    middle_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    plain_password = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    roles = relationship("UserRole", back_populates="user")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    student_tasks = relationship("StudentTask", back_populates="student")
    uploaded_media = relationship("TaskMedia", back_populates="teacher")


# ================================
# Связь пользователь ↔ роль
# ================================
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


# ================================
# Профиль студента
# ================================
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    image_url = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    rating_points = Column(Integer, default=0)
    last_rank = Column(Integer)
    level = Column(Text, default="beginner")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="student_profile")


# ================================
# Категории
# ================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)

    tasks = relationship("Task", back_populates="category")


# ================================
# Задания
# ================================
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    video_url = Column(Text)  # демонстрационное видео (от студии)
    difficulty = Column(Integer, default=1)
    max_score = Column(Integer, default=100)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="tasks")
    student_tasks = relationship("StudentTask", back_populates="task")


# ================================
# Задания студентов
# ================================
class StudentTask(Base):
    __tablename__ = "student_tasks"
    __table_args__ = (
        UniqueConstraint("student_id", "task_id", name="uq_student_task"),
        Index("idx_student_tasks_student_id", "student_id"),
        Index("idx_student_tasks_task_id", "task_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))

    status = Column(Text, default="not_started")
    score = Column(Integer, default=0)
    comment = Column(Text)

    submitted_at = Column(TIMESTAMP(timezone=True))
    reviewed_at = Column(TIMESTAMP(timezone=True))

    student = relationship("User", back_populates="student_tasks")
    task = relationship("Task", back_populates="student_tasks")
    media = relationship("TaskMedia", back_populates="student_task")


# ================================
# Видео выполнения (ключевая таблица)
# ================================
class TaskMedia(Base):
    __tablename__ = "task_media"
    __table_args__ = (
        Index("idx_task_media_student_task_id", "student_task_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    student_task_id = Column(
        Integer,
        ForeignKey("student_tasks.id", ondelete="CASCADE"),
        nullable=False
    )

    video_url = Column(Text, nullable=False)  # MinIO object name или URL
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_public = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    student_task = relationship("StudentTask", back_populates="media")
    teacher = relationship("User", back_populates="uploaded_media")


# ================================
# Галерея
# ================================
class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ================================
# История рейтинга
# ================================
class RatingsHistory(Base):
    __tablename__ = "ratings_history"
    __table_args__ = (
        Index("idx_ratings_student_id", "student_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    points_change = Column(Integer, nullable=False)
    reason = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ================================
# Достижения (мероприятия)
# ================================
class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    event_date = Column(TIMESTAMP(timezone=True))
    place = Column(Text)  # место/результат
    is_collective = Column(Boolean, default=False)  # коллективное достижение
    certificate_url = Column(Text)  # ссылка на грамоту (PDF/PNG)
    video_url = Column(Text)  # ссылка на видео достижения

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    users = relationship("UserAchievement", back_populates="achievement")


# ================================
# Связь пользователь ↔ достижение
# ================================
class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))

    awarded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User")
    achievement = relationship("Achievement", back_populates="users")