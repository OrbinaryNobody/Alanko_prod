from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from attendance.dtos.attendance_dto import AttendancePayload
from attendance.facade import attendance_facade
from attendance.schemas import AttendanceCheckInCreate, SubscriptionCreate
from attendance.schemas_response import AttendanceHistoryResponse
from core.access import AccessContext
from core.exceptions import DomainError
from core.http import translate_domain_error
from core.permissions import require_manage_attendance, require_view_attendance
from db.database import get_db
from education.facade import education_facade
from education.exceptions.domain_exceptions import EducationError


router = APIRouter(prefix="/attendance", tags=["attendance"])
student_router = APIRouter(prefix="/attendance", tags=["attendance"])


def _attendance_payload(record):
    return AttendancePayload(
        id=record.id,
        student_id=record.student_id,
        group_id=record.group_id,
        attendance_date=record.attendance_date.isoformat(),
        checked_in_at=record.checked_in_at.isoformat() if record.checked_in_at else None,
        status=record.status,
        marked_by=record.marked_by,
        comment=record.comment,
    ).to_dict()


@router.get("/summary")
def get_summary(
    attendance_date: date = Query(..., alias="date"),
    ctx: AccessContext = Depends(require_view_attendance),
    db: Session = Depends(get_db),
):
    return attendance_facade.get_summary(db, attendance_date=attendance_date).to_dict()


@router.post("/check-in", status_code=201)
def check_in(
    data: AttendanceCheckInCreate,
    ctx: AccessContext = Depends(require_manage_attendance),
    db: Session = Depends(get_db),
):
    try:
        record = attendance_facade.check_in(
            db,
            ctx=ctx,
            student_id=data.student_id,
            group_id=data.group_id,
            attendance_date=data.attendance_date,
            marked_by=ctx.user_id,
            comment=data.comment,
        )
    except DomainError as exc:
        translate_domain_error(exc)
    return _attendance_payload(record)


@router.post("/{attendance_id}/cancel")
def cancel_attendance(
    attendance_id: int,
    ctx: AccessContext = Depends(require_manage_attendance),
    db: Session = Depends(get_db),
):
    try:
        record = attendance_facade.cancel(db, ctx=ctx, attendance_id=attendance_id)
    except DomainError as exc:
        translate_domain_error(exc)
    return _attendance_payload(record)


@student_router.get("/students/{student_id}/attendance", response_model=AttendanceHistoryResponse)
def get_student_history(
    student_id: int,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ctx: AccessContext = Depends(require_view_attendance),
    db: Session = Depends(get_db),
):
    records = attendance_facade.list_history(db, ctx=ctx, student_id=student_id, date_from=date_from, date_to=date_to, limit=limit, offset=offset)
    return {"student_id": student_id, "items": [_attendance_payload(record) for record in records]}


@router.post("/students/{student_id}/subscriptions", status_code=201)
def create_subscription(
    student_id: int,
    data: SubscriptionCreate,
    ctx: AccessContext = Depends(require_manage_attendance),
    db: Session = Depends(get_db),
):
    try:
        subscription = attendance_facade.create_subscription(
            db,
            student_id=student_id,
            plan_name=data.plan_name,
            total_visits=data.total_visits,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            payment_status=data.payment_status,
            amount=data.amount,
            currency=data.currency,
        )
    except DomainError as exc:
        translate_domain_error(exc)
    return {
        "id": subscription.id,
        "student_id": subscription.student_id,
        "plan_name": subscription.plan_name,
        "total_visits": subscription.total_visits,
        "remaining_visits": subscription.remaining_visits,
        "valid_from": subscription.valid_from.isoformat(),
        "valid_until": subscription.valid_until.isoformat(),
        "status": subscription.status,
        "payment_status": subscription.payment_status,
        "amount": subscription.amount,
        "currency": subscription.currency,
    }


@router.post("/groups/{group_id}/subscriptions", status_code=201)
def create_group_subscriptions(
    group_id: int,
    data: SubscriptionCreate,
    ctx: AccessContext = Depends(require_manage_attendance),
    db: Session = Depends(get_db),
):
    try:
        group_students = education_facade.get_group_students(db, ctx=ctx, group_id=group_id)
        student_ids = [student.student_id for student in group_students if student.status == "active"]
        subscriptions = attendance_facade.create_subscriptions_for_students(
            db,
            student_ids=student_ids,
            plan_name=data.plan_name,
            total_visits=data.total_visits,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            payment_status=data.payment_status,
            amount=data.amount,
            currency=data.currency,
        )
    except (DomainError, EducationError) as exc:
        translate_domain_error(exc)

    return {
        "group_id": group_id,
        "count": len(subscriptions),
        "subscriptions": [
            {
                "id": subscription.id,
                "student_id": subscription.student_id,
                "plan_name": subscription.plan_name,
                "total_visits": subscription.total_visits,
                "remaining_visits": subscription.remaining_visits,
                "valid_from": subscription.valid_from.isoformat(),
                "valid_until": subscription.valid_until.isoformat(),
                "status": subscription.status,
                "payment_status": subscription.payment_status,
                "amount": subscription.amount,
                "currency": subscription.currency,
            }
            for subscription in subscriptions
        ],
    }


@router.post("/students/{student_id}/subscriptions/renew", status_code=201)
def renew_subscription(
    student_id: int,
    data: SubscriptionCreate,
    ctx: AccessContext = Depends(require_manage_attendance),
    db: Session = Depends(get_db),
):
    try:
        subscription = attendance_facade.create_subscription(
            db,
            student_id=student_id,
            plan_name=data.plan_name,
            total_visits=data.total_visits,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            payment_status=data.payment_status,
            amount=data.amount,
            currency=data.currency,
        )
    except DomainError as exc:
        translate_domain_error(exc)
    return {
        "id": subscription.id,
        "student_id": subscription.student_id,
        "plan_name": subscription.plan_name,
        "total_visits": subscription.total_visits,
        "remaining_visits": subscription.remaining_visits,
        "valid_from": subscription.valid_from.isoformat(),
        "valid_until": subscription.valid_until.isoformat(),
        "status": subscription.status,
        "payment_status": subscription.payment_status,
        "amount": subscription.amount,
        "currency": subscription.currency,
    }