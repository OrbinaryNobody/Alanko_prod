from sqlalchemy import Boolean, Column, Date, Integer, Text, TIMESTAMP, String, ForeignKey, Time, JSON
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
    change_proposals = relationship("ProgramChangeProposal", back_populates="program", cascade="all, delete-orphan")


class ProgramChangeProposal(Base):
    __tablename__ = "program_change_proposals"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=True, index=True)
    proposal_type = Column(String(16), nullable=False, default="UPDATE", index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="PENDING", index=True)
    base_snapshot = Column(JSON, nullable=False)
    proposed_snapshot = Column(JSON, nullable=False)
    author_comment = Column(Text)
    reviewer_comment = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reviewed_at = Column(TIMESTAMP(timezone=True))

    program = relationship("Program", back_populates="change_proposals")


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
    topics = relationship("ProgramTopic", back_populates="block", cascade="all, delete-orphan", order_by="ProgramTopic.order")
    tasks = relationship("ProgramTask", back_populates="block", cascade="all, delete-orphan")


class ProgramTopic(Base):
    __tablename__ = "program_topics"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("program_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    status = Column(Text, default="draft")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    block = relationship("ProgramBlock", back_populates="topics")
    tasks = relationship("ProgramTask", back_populates="topic", cascade="all, delete-orphan", order_by="ProgramTask.order")
    materials = relationship("ProgramMaterial", back_populates="topic", cascade="all, delete-orphan")


class ProgramTask(Base):
    __tablename__ = "program_tasks"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("program_blocks.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("program_topics.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    max_score = Column(Integer, default=100)
    order = Column(Integer, default=0)
    is_manual = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    block = relationship("ProgramBlock", back_populates="tasks")
    topic = relationship("ProgramTopic", back_populates="tasks")
    materials = relationship("ProgramMaterial", back_populates="task", cascade="all, delete-orphan")


class ProgramMaterial(Base):
    __tablename__ = "program_materials"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("program_topics.id", ondelete="CASCADE"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("program_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    file_url = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)
    content_type = Column(String(128), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    topic = relationship("ProgramTopic", back_populates="materials")
    task = relationship("ProgramTask", back_populates="materials")


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
    leaderboard_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    program = relationship("Program", back_populates="groups")
    current_block = relationship("ProgramBlock", foreign_keys=[current_block_id])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    enrollments = relationship("GroupEnrollment", back_populates="group", cascade="all, delete-orphan")
    schedules = relationship("GroupSchedule", back_populates="group", cascade="all, delete-orphan")


class GroupSchedule(Base):
    __tablename__ = "group_schedules"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    status = Column(String(16), nullable=False, default="ACTIVE")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="schedules")
    teacher = relationship("User", foreign_keys=[teacher_id])


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
    media = relationship("TaskMedia", back_populates="group_student_task", cascade="all, delete-orphan")
