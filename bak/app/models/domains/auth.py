from enum import Enum

from sqlalchemy import Column, Integer, Text, TIMESTAMP, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text)
    middle_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    image_url = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    student_tasks = relationship("StudentTask", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    uploaded_media = relationship("TaskMedia", back_populates="teacher")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
