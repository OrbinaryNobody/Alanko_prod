from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session

from consultations.facade import consultations_facade
from consultations.facade import consultations_facade
from consultations.dtos import AttendancePayload, InvitationPayload
from core.access import AccessContext
from core.exceptions import DomainError
from core.http import translate_domain_error
from core.permissions import Permission, require_any_permission
from db.database import get_db
from schemas.consultations import ConsultationAttendanceUpdate, ConsultationDayCreate, ConsultationDayStatusUpdate, ConsultationInvitationCreate, ConsultationPaymentUpdate, ConsultationSlotCreate

router = APIRouter(prefix="/consultations/admin", tags=["consultations-admin"])


@router.get("/days")
def list_days(
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    days = consultations_facade.list_days(db)
    return {
        "items": [
            {
                "id": day.id,
                "date": day.date.isoformat(),
                "status": day.status,
                "available_from": day.available_from.isoformat() if day.available_from else None,
                "available_to": day.available_to.isoformat() if day.available_to else None,
            }
            for day in days
        ]
    }


@router.post("/days", status_code=201)
def create_day(
    data: ConsultationDayCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    day = consultations_facade.create_day(
        db,
        date_value=data.date,
        status=data.status,
        available_from=data.available_from,
        available_to=data.available_to,
    )
    return {
        "id": day.id,
        "date": day.date.isoformat(),
        "status": day.status,
        "available_from": day.available_from.isoformat() if day.available_from else None,
        "available_to": day.available_to.isoformat() if day.available_to else None,
    }


@router.patch("/days/{day_id}/status")
def set_day_status(
    day_id: int,
    data: ConsultationDayStatusUpdate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    day = consultations_facade.set_day_status(db, day_id=day_id, status=data.status)
    return {
        "id": day.id,
        "status": day.status,
    }


@router.get("/slots")
def list_slots(
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    slots = consultations_facade.list_slots(db)
    return {
        "items": [
            {
                "id": slot.id,
                "day_id": slot.day_id,
                "teacher_id": slot.teacher_id,
                "start_at": slot.start_at.isoformat() if slot.start_at else None,
                "end_at": slot.end_at.isoformat() if slot.end_at else None,
                "capacity": slot.capacity,
                "price": slot.price,
                "currency": slot.currency,
                "access_mode": slot.access_mode,
                "status": slot.status,
            }
            for slot in slots
        ]
    }


@router.post("/slots", status_code=201)
def create_slot(
    data: ConsultationSlotCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    slot = consultations_facade.create_slot(
        db,
        day_id=data.day_id,
        teacher_id=data.teacher_id,
        start_at=data.start_at,
        end_at=data.end_at,
        capacity=data.capacity,
        price=data.price,
        currency=data.currency,
        access_mode=data.access_mode,
        created_by=ctx.user_id,
    )
    return {
        "id": slot.id,
        "day_id": slot.day_id,
        "teacher_id": slot.teacher_id,
        "start_at": slot.start_at.isoformat() if slot.start_at else None,
        "end_at": slot.end_at.isoformat() if slot.end_at else None,
        "capacity": slot.capacity,
        "price": slot.price,
        "currency": slot.currency,
        "access_mode": slot.access_mode,
    }


@router.post("/slots/{slot_id}/invitations", status_code=201)
def create_invitations(
    slot_id: int,
    data: ConsultationInvitationCreate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    try:
        invitations = consultations_facade.create_invitations(
            db,
            ctx=ctx,
            slot_id=slot_id,
            student_ids=data.student_ids,
        )
    except DomainError as exc:
        translate_domain_error(exc)

    return {"items": [InvitationPayload(
        id=invitation.id,
        slot_id=invitation.slot_id,
        student_id=invitation.student_id,
        status=invitation.status,
        created_at=invitation.created_at,
        responded_at=invitation.responded_at,
    ).to_dict() for invitation in invitations]}


@router.patch("/participants/{participant_id}/attendance")
def set_attendance_status(
    participant_id: int,
    data: ConsultationAttendanceUpdate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    try:
        participant = consultations_facade.set_attendance_status(
            db,
            ctx=ctx,
            participant_id=participant_id,
            status=data.status,
        )
    except DomainError as exc:
        translate_domain_error(exc)

    return AttendancePayload(
        id=participant.id,
        slot_id=participant.slot_id,
        student_id=participant.student_id,
        booking_status=participant.booking_status,
        attendance_status=participant.attendance_status,
        payment_status=participant.payment_status,
    ).to_dict()


@router.get("/slots/{slot_id}/participants")
def list_slot_participants(
    slot_id: int,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    try:
        participants = consultations_facade.get_slot_participants(db, ctx=ctx, slot_id=slot_id)
    except DomainError as exc:
        translate_domain_error(exc)

    return {"items": [AttendancePayload(
        id=participant.id,
        slot_id=participant.slot_id,
        student_id=participant.student_id,
        booking_status=participant.booking_status,
        attendance_status=participant.attendance_status,
        payment_status=participant.payment_status,
    ).to_dict() for participant in participants]}


@router.patch("/participants/{participant_id}/payment")
def set_payment_status(
    participant_id: int,
    data: ConsultationPaymentUpdate,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    try:
        participant = consultations_facade.set_payment_status(
            db,
            ctx=ctx,
            participant_id=participant_id,
            status=data.status,
        )
    except DomainError as exc:
        translate_domain_error(exc)

    return AttendancePayload(
        id=participant.id,
        slot_id=participant.slot_id,
        student_id=participant.student_id,
        booking_status=participant.booking_status,
        attendance_status=participant.attendance_status,
        payment_status=participant.payment_status,
    ).to_dict()


@router.get("/slots/{slot_id}/settlement")
def get_settlement_summary(
    slot_id: int,
    ctx: AccessContext = Depends(require_any_permission(Permission.MANAGE_CONSULTATIONS, Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    try:
        return consultations_facade.get_settlement_summary(db, ctx=ctx, slot_id=slot_id)
    except DomainError as exc:
        translate_domain_error(exc)
