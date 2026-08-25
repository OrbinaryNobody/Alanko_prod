from datetime import date

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from attendance.dtos.attendance_dto import AttendanceSummaryPayload
from attendance.repositories.attendance_repository import attendance_repository
from models.domains.attendance import AttendanceRecord, Subscription
from models.domains.auth import Role, User


class AttendanceSummaryService:
    def get_summary(self, db: Session, *, attendance_date: date):
        students = db.query(User.id).join(User.roles).filter(Role.name == "student").subquery()
        active_subscription = (
            db.query(
                Subscription.student_id.label("student_id"),
                func.row_number().over(
                    partition_by=Subscription.student_id,
                    order_by=(Subscription.valid_until.desc(), Subscription.id.desc()),
                ).label("row_number"),
                Subscription.payment_status,
                Subscription.remaining_visits,
            )
            .filter(
                Subscription.status == "ACTIVE",
                Subscription.valid_from <= attendance_date,
                Subscription.valid_until >= attendance_date,
            )
            .subquery()
        )
        summary = (
            db.query(
                func.count(students.c.id).label("total_students"),
                func.count(func.distinct(case((AttendanceRecord.status == "PRESENT", AttendanceRecord.student_id)))).label("checked_count"),
                func.count(func.distinct(case((
                    (active_subscription.c.row_number == 1)
                    & (active_subscription.c.payment_status == "PAID")
                    & (active_subscription.c.remaining_visits > 0),
                    active_subscription.c.student_id,
                )))).label("active_subscriptions"),
                func.count(func.distinct(case((
                    (active_subscription.c.row_number == 1)
                    & (active_subscription.c.remaining_visits > 0)
                    & (active_subscription.c.remaining_visits <= 2),
                    active_subscription.c.student_id,
                )))).label("warning_subscriptions"),
            )
            .select_from(students)
            .outerjoin(AttendanceRecord, (AttendanceRecord.student_id == students.c.id) & (AttendanceRecord.attendance_date == attendance_date))
            .outerjoin(active_subscription, (active_subscription.c.student_id == students.c.id) & (active_subscription.c.row_number == 1))
            .one()
        )
        paid_active = db.query(func.count(func.distinct(active_subscription.c.student_id))).select_from(active_subscription).filter(
            active_subscription.c.row_number == 1,
            active_subscription.c.payment_status == "PAID",
            active_subscription.c.remaining_visits > 0,
        ).scalar() or 0
        debt_count = summary.total_students - paid_active

        return AttendanceSummaryPayload(
            date=attendance_date.isoformat(),
            checked_count=summary.checked_count,
            total_students=summary.total_students,
            active_subscriptions=paid_active,
            warning_subscriptions=summary.warning_subscriptions,
            debt_count=debt_count,
        )


attendance_summary_service = AttendanceSummaryService()