from sqlalchemy import Boolean, Column, Integer, Text, TIMESTAMP, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import Base


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
    role = Column(String(32), nullable=False, default="teacher")

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
