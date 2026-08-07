from sqlalchemy.orm import Session

from models.domains.auth import User
from models.domains.education import Group, GroupEnrollment, GroupMember, GroupStudentTask, Program, ProgramBlock, ProgramTask


class GroupRepository:
    def get_by_id(self, db: Session, group_id: int) -> Group | None:
        return db.query(Group).filter(Group.id == group_id).first()

    def list_for_user(self, db: Session, *, user_id: int, is_admin: bool = False) -> list[Group]:
        if is_admin:
            return db.query(Group).order_by(Group.created_at.desc()).all()
        return (
            db.query(Group)
            .join(Group.members)
            .filter(GroupMember.user_id == user_id)
            .order_by(Group.created_at.desc())
            .all()
        )

    def get_program_by_id(self, db: Session, program_id: int) -> Program | None:
        return db.query(Program).filter(Program.id == program_id).first()

    def create(self, db: Session, group: Group) -> Group:
        db.add(group)
        db.flush()
        db.refresh(group)
        return group

    def create_member(self, db: Session, member: GroupMember) -> GroupMember:
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    def get_member(self, db: Session, *, group_id: int, user_id: int) -> GroupMember | None:
        return db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id).first()

    def get_enrollment(self, db: Session, *, group_id: int, student_id: int) -> GroupEnrollment | None:
        return db.query(GroupEnrollment).filter(GroupEnrollment.group_id == group_id, GroupEnrollment.student_id == student_id).first()

    def create_enrollment(self, db: Session, enrollment: GroupEnrollment) -> GroupEnrollment:
        db.add(enrollment)
        db.flush()
        db.refresh(enrollment)
        return enrollment

    def list_program_tasks(self, db: Session, *, program_id: int) -> list[ProgramTask]:
        return db.query(ProgramTask).join(ProgramBlock).filter(ProgramBlock.program_id == program_id).all()

    def create_group_student_tasks(self, db: Session, tasks: list[GroupStudentTask]) -> list[GroupStudentTask]:
        if tasks:
            db.bulk_save_objects(tasks)
            db.flush()
        return tasks

    def list_enrollments(self, db: Session, *, group_id: int) -> list[GroupEnrollment]:
        return (
            db.query(GroupEnrollment)
            .filter(GroupEnrollment.group_id == group_id)
            .order_by(GroupEnrollment.joined_at.desc())
            .all()
        )


group_repository = GroupRepository()
