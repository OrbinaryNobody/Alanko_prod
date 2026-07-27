from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Group, GroupEnrollment, GroupMember, GroupRole, GroupStudentTask, Program, ProgramBlock, ProgramTask, User


class GroupService:
    def ensure_group_access(self, db: Session, *, group_id: int, user_id: int, is_admin: bool = False):
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if not is_admin and group.created_by != user_id and not any(member.user_id == user_id for member in group.members):
            raise HTTPException(status_code=403, detail="Access denied to this group")
        return group

    def create_group(self, db: Session, *, title: str, description: str | None, program_id: int | None, created_by: int):
        program = None
        if program_id is not None:
            program = db.query(Program).filter(Program.id == program_id).first()
            if not program:
                raise HTTPException(status_code=404, detail="Program not found")

        group = Group(title=title, description=description, program_id=program.id if program else None, created_by=created_by)
        db.add(group)
        db.commit()
        db.refresh(group)

        member = GroupMember(group_id=group.id, user_id=created_by, role=GroupRole.TEACHER.value)
        db.add(member)
        db.commit()
        return group

    def get_groups_for_user(self, db: Session, user_id: int):
        return (
            db.query(Group)
            .join(Group.members)
            .filter(GroupMember.user_id == user_id)
            .order_by(Group.created_at.desc())
            .all()
        )

    def add_member(self, db: Session, *, group_id: int, user_id: int, role: str, actor_id: int, is_admin: bool = False):
        group = self.ensure_group_access(db, group_id=group_id, user_id=actor_id, is_admin=is_admin)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        existing = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id).first()
        if existing:
            existing.role = role
            db.commit()
            return existing

        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        db.add(member)
        db.commit()
        return member

    def enroll_student(self, db: Session, *, group_id: int, student_id: int, actor_id: int, is_admin: bool = False):
        group = self.ensure_group_access(db, group_id=group_id, user_id=actor_id, is_admin=is_admin)

        existing = db.query(GroupEnrollment).filter(GroupEnrollment.group_id == group_id, GroupEnrollment.student_id == student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student already enrolled")

        enrollment = GroupEnrollment(group_id=group_id, student_id=student_id, status="active")
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        if group.program_id:
            tasks = db.query(ProgramTask).join(ProgramBlock).filter(ProgramBlock.program_id == group.program_id).all()
            for task in tasks:
                db.add(GroupStudentTask(enrollment_id=enrollment.id, program_task_id=task.id, status="assigned"))
            db.commit()

        return enrollment

    def get_group_students(self, db: Session, group_id: int, actor_id: int, is_admin: bool = False):
        self.ensure_group_access(db, group_id=group_id, user_id=actor_id, is_admin=is_admin)
        enrollments = (
            db.query(GroupEnrollment)
            .filter(GroupEnrollment.group_id == group_id)
            .order_by(GroupEnrollment.joined_at.desc())
            .all()
        )
        return [
            {
                "id": enrollment.id,
                "student_id": enrollment.student_id,
                "status": enrollment.status,
                "current_block_id": enrollment.current_block_id,
                "completion_percent": enrollment.completion_percent,
            }
            for enrollment in enrollments
        ]


group_service = GroupService()
