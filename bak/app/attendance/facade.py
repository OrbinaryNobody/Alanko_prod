from datetime import date

from sqlalchemy.orm import Session

from attendance.repositories.attendance_repository import attendance_repository
from attendance.services.subscription_service import subscription_service
from attendance.services.summary_service import attendance_summary_service
from attendance.services.parent_service import parent_service


class AttendanceFacade:
    def list_students(self, db: Session, *, search: str | None = None, group_id: int | None = None, limit: int | None = 100, offset: int = 0):
        return attendance_repository.list_students(db, search=search, group_id=group_id, limit=limit, offset=offset)

    def get_student_context(self, db: Session, *, student_id: int, attendance_date: date):
        return {
            "groups": attendance_repository.list_student_groups(db, student_id=student_id),
            "parent": attendance_repository.get_primary_parent(db, student_id=student_id),
            "subscription": attendance_repository.get_active_subscription(db, student_id=student_id, on_date=attendance_date),
            "attendance": attendance_repository.get_attendance(db, student_id=student_id, attendance_date=attendance_date),
        }

    def check_in(self, db: Session, *, ctx, **kwargs):
        kwargs["ctx"] = ctx
        return attendance_service.check_in(db, **kwargs)

    def cancel(self, db: Session, *, ctx, attendance_id: int):
        return attendance_service.cancel(db, ctx=ctx, attendance_id=attendance_id)

    def list_history(self, db: Session, *, ctx, student_id: int, date_from: date | None, date_to: date | None, limit: int = 50, offset: int = 0):
        return attendance_service.list_history(db, ctx=ctx, student_id=student_id, date_from=date_from, date_to=date_to, limit=limit, offset=offset)

    def get_summary(self, db: Session, *, attendance_date: date):
        return attendance_summary_service.get_summary(db, attendance_date=attendance_date)

    def create_subscription(self, db: Session, *, student_id: int, **kwargs):
        return subscription_service.create(db, student_id=student_id, **kwargs)

    def create_subscriptions_for_students(self, db: Session, *, student_ids: list[int], **kwargs):
        return subscription_service.create_for_students(db, student_ids=student_ids, **kwargs)

    def attach_parent(self, db: Session, *, student_id: int, **kwargs):
        return parent_service.attach_parent(db, student_id=student_id, **kwargs)


attendance_facade = AttendanceFacade()