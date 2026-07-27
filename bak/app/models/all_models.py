from enum import Enum
from sqlalchemy import (
    Boolean, Column, Integer, Text, TIMESTAMP, String,
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


class GroupRole(str, Enum):
    TEACHER = "teacher"
    ASSISTANT = "assistant"
    CURATOR = "curator"
    OBSERVER = "observer"


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
# Программы обучения
# ================================
class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(Text, default="draft")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    blocks = relationship("ProgramBlock", back_populates="program", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="program")


class ProgramBlock(Base):
    __tablename__ = "program_blocks"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    status = Column(Text, default="draft")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    program = relationship("Program", back_populates="blocks")
    tasks = relationship("ProgramTask", back_populates="block", cascade="all, delete-orphan")


class ProgramTask(Base):
    __tablename__ = "program_tasks"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("program_blocks.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    max_score = Column(Integer, default=100)
    is_manual = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    block = relationship("ProgramBlock", back_populates="tasks")


# ================================
# Группы и зачисления
# ================================
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"))
    current_block_id = Column(Integer, ForeignKey("program_blocks.id", ondelete="SET NULL"))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(Text, default="active")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    program = relationship("Program", back_populates="groups")
    current_block = relationship("ProgramBlock", foreign_keys=[current_block_id])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    enrollments = relationship("GroupEnrollment", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(32), nullable=False, default=GroupRole.TEACHER.value)

    group = relationship("Group", back_populates="members")


class GroupEnrollment(Base):
    __tablename__ = "group_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    left_at = Column(TIMESTAMP(timezone=True))
    status = Column(Text, default="active")
    current_block_id = Column(Integer, ForeignKey("program_blocks.id", ondelete="SET NULL"))
    completed_blocks = Column(Integer, default=0)
    completion_percent = Column(Integer, default=0)

    group = relationship("Group", back_populates="enrollments")
    current_block = relationship("ProgramBlock", foreign_keys=[current_block_id])
    tasks = relationship("GroupStudentTask", back_populates="enrollment", cascade="all, delete-orphan")


class GroupStudentTask(Base):
    __tablename__ = "group_student_tasks"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("group_enrollments.id", ondelete="CASCADE"), nullable=False)
    program_task_id = Column(Integer, ForeignKey("program_tasks.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, default="assigned")
    assigned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    submitted_at = Column(TIMESTAMP(timezone=True))
    checked_at = Column(TIMESTAMP(timezone=True))
    grade = Column(Integer)
    feedback = Column(Text)

    enrollment = relationship("GroupEnrollment", back_populates="tasks")
    program_task = relationship("ProgramTask")


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