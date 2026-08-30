from sqlalchemy import Boolean, Column, Integer, Text, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    image_url = Column(Text, default="default.jpg")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    birth_year = Column(Integer, nullable=True)
    rating_points = Column(Integer, default=0)
    last_rank = Column(Integer)
    level = Column(Text, default="beginner")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="student_profile")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    video_url = Column(Text)
    difficulty = Column(Integer, default=1)
    max_score = Column(Integer, default=100)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    student_tasks = relationship("StudentTask", back_populates="task")


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


class TaskMedia(Base):
    __tablename__ = "task_media"
    __table_args__ = (
        Index("idx_task_media_student_task_id", "student_task_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_task_id = Column(Integer, ForeignKey("student_tasks.id", ondelete="CASCADE"), nullable=True)
    group_student_task_id = Column(Integer, ForeignKey("group_student_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    video_url = Column(Text, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_public = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    student_task = relationship("StudentTask", back_populates="media")
    group_student_task = relationship("GroupStudentTask", back_populates="media")
    teacher = relationship("User", back_populates="uploaded_media")


class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


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
