from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from models.domains.attendance import AttendanceRecord, ParentGuardian, StudentParent, Subscription
from models.domains.auth import Role, User, UserRole
from models.domains.education import Group, GroupEnrollment


class AttendanceRepository:
    def list_students(self, db: Session, *, search: str | None = None, group_id: int | None = None, limit: int | None = 100, offset: int = 0):
        query = (
            db.query(User)
            .join(User.roles)
            .filter(Role.name == "student")
            .filter(~User.roles.any(UserRole.role.has(Role.name.in_(("admin", "teacher", "secretary")))))
            .options(joinedload(User.student_profile))
            .distinct()
        )
        if group_id is not None:
            query = query.join(GroupEnrollment, GroupEnrollment.student_id == User.id).filter(
                GroupEnrollment.group_id == group_id,
                GroupEnrollment.status == "active",
            )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.outerjoin(StudentParent, StudentParent.student_id == User.id).outerjoin(
                ParentGuardian, ParentGuardian.id == StudentParent.parent_id
            ).filter(or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.middle_name.ilike(pattern),
                ParentGuardian.first_name.ilike(pattern),
                ParentGuardian.last_name.ilike(pattern),
                ParentGuardian.phone.ilike(pattern),
            ))
        query = query.order_by(User.last_name, User.first_name)
        if limit is not None:
            query = query.offset(offset).limit(limit)
        return query.all()

    def list_student_groups(self, db: Session, *, student_id: int):
        return (
            db.query(Group)
            .join(GroupEnrollment, GroupEnrollment.group_id == Group.id)
            .filter(GroupEnrollment.student_id == student_id, GroupEnrollment.status == "active")
            .order_by(Group.title)
            .all()
        )

    def get_primary_parent(self, db: Session, *, student_id: int):
        return (
            db.query(ParentGuardian)
            .join(StudentParent, StudentParent.parent_id == ParentGuardian.id)
            .filter(StudentParent.student_id == student_id)
            .order_by(StudentParent.is_primary.desc(), ParentGuardian.id)
            .first()
        )

    def get_active_subscription(self, db: Session, *, student_id: int, on_date: date):
        return (
            db.query(Subscription)
            .filter(
                Subscription.student_id == student_id,
                Subscription.status == "ACTIVE",
                Subscription.valid_from <= on_date,
                Subscription.valid_until >= on_date,
            )
            .order_by(Subscription.valid_until.desc(), Subscription.id.desc())
            .first()
        )

    def get_attendance(self, db: Session, *, student_id: int, attendance_date: date, group_id: int | None = None):
        query = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date == attendance_date,
        )
        if group_id is not None:
            query = query.filter(AttendanceRecord.group_id == group_id)
        return query.order_by(AttendanceRecord.id.desc()).first()

    def list_attendance(self, db: Session, *, student_id: int, date_from: date | None, date_to: date | None, limit: int = 50, offset: int = 0):
        query = db.query(AttendanceRecord).options(
            joinedload(AttendanceRecord.group),
            joinedload(AttendanceRecord.marker),
        ).filter(AttendanceRecord.student_id == student_id)
        if date_from is not None:
            query = query.filter(AttendanceRecord.attendance_date >= date_from)
        if date_to is not None:
            query = query.filter(AttendanceRecord.attendance_date <= date_to)
        return query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.checked_in_at.desc()).offset(offset).limit(limit).all()

    def get_subscription_for_update(self, db: Session, *, student_id: int, on_date: date):
        return (
            db.query(Subscription)
            .filter(
                Subscription.student_id == student_id,
                Subscription.status == "ACTIVE",
                Subscription.valid_from <= on_date,
                Subscription.valid_until >= on_date,
            )
            .with_for_update()
            .order_by(Subscription.valid_until.desc(), Subscription.id.desc())
            .first()
        )

    def create_attendance(self, db: Session, record: AttendanceRecord):
        db.add(record)
        db.flush()
        db.refresh(record)
        return record


attendance_repository = AttendanceRepository()