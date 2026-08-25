from datetime import date, datetime

from sqlalchemy.orm import Session

from attendance.repositories.attendance_repository import attendance_repository
from core.exceptions import ConflictError, NotFoundError, PermissionDenied
from models.domains.attendance import AttendanceRecord, Subscription
from models.domains.education import GroupEnrollment, GroupMember
from shared.unit_of_work import UnitOfWork


class AttendanceService:
    def _has_group_access(self, db: Session, *, ctx, student_id: int, group_id: int | None = None) -> bool:
        if ctx.is_admin or ctx.has_role("secretary"):
            return True
        query = (
            db.query(GroupEnrollment)
            .join(GroupMember, GroupMember.group_id == GroupEnrollment.group_id)
            .filter(
                GroupEnrollment.student_id == student_id,
                GroupEnrollment.status == "active",
                GroupMember.user_id == ctx.user_id,
            )
        )
        if group_id is not None:
            query = query.filter(GroupEnrollment.group_id == group_id)
        return query.first() is not None

    def _require_manage_access(self, db: Session, *, ctx, student_id: int, group_id: int | None = None):
        if not self._has_group_access(db, ctx=ctx, student_id=student_id, group_id=group_id):
            raise PermissionDenied("Access denied to this student's attendance")

    def check_in(self, db: Session, *, ctx, student_id: int, group_id: int | None, attendance_date: date, marked_by: int, comment: str | None = None):
        self._require_manage_access(db, ctx=ctx, student_id=student_id, group_id=group_id)
        with UnitOfWork(db):
            existing = attendance_repository.get_attendance(db, student_id=student_id, attendance_date=attendance_date, group_id=group_id)
            if existing and existing.status == "PRESENT":
                raise ConflictError("Attendance is already marked")

            subscription = attendance_repository.get_subscription_for_update(db, student_id=student_id, on_date=attendance_date)
            if not subscription:
                raise ConflictError("Student has no active subscription")
            if subscription.remaining_visits <= 0:
                raise ConflictError("Subscription has no remaining visits")

            if existing and existing.status == "CANCELLED":
                existing.status = "PRESENT"
                existing.checked_in_at = datetime.now().astimezone()
                existing.marked_by = marked_by
                existing.comment = comment
                existing.subscription_id = subscription.id
                record = existing
            else:
                record = attendance_repository.create_attendance(db, AttendanceRecord(
                    student_id=student_id,
                    group_id=group_id,
                    subscription_id=subscription.id,
                    attendance_date=attendance_date,
                    status="PRESENT",
                    marked_by=marked_by,
                    comment=comment,
                ))

            subscription.remaining_visits -= 1
            if subscription.remaining_visits == 0:
                subscription.status = "EXHAUSTED"
            db.flush()
            return record

    def cancel(self, db: Session, *, ctx, attendance_id: int):
        with UnitOfWork(db):
            record = db.query(AttendanceRecord).filter(AttendanceRecord.id == attendance_id).with_for_update().first()
            if not record:
                raise NotFoundError("Attendance record not found")
            self._require_manage_access(db, ctx=ctx, student_id=record.student_id, group_id=record.group_id)
            if record.status == "CANCELLED":
                return record
            record.status = "CANCELLED"
            if record.subscription_id:
                subscription = db.query(Subscription).filter(Subscription.id == record.subscription_id).with_for_update().first()
                if subscription:
                    subscription.remaining_visits += 1
                    if subscription.status == "EXHAUSTED":
                        subscription.status = "ACTIVE"
            db.flush()
            return record

    def list_history(self, db: Session, *, ctx, student_id: int, date_from: date | None, date_to: date | None, limit: int = 50, offset: int = 0):
        if not ctx.is_admin and ctx.user_id != student_id and not self._has_group_access(db, ctx=ctx, student_id=student_id):
            raise PermissionDenied("Access denied to this student's attendance")
        return attendance_repository.list_attendance(db, student_id=student_id, date_from=date_from, date_to=date_to, limit=limit, offset=offset)


attendance_service = AttendanceService()