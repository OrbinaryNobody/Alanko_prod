from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from consultations.dtos import InvitationPayload, NotificationPayload, ParticipantPayload
from consultations.facade import consultations_facade
from core.access import AccessContext
from core.exceptions import DomainError
from core.http import translate_domain_error
from core.permissions import Permission, require_permission, require_student_consultation_booking
from db.database import get_db

router = APIRouter(prefix="/consultations", tags=["consultations"]) 


@router.get("/availability")
def get_availability(
    date_from: date | None = Query(default=None, alias="date_from"),
    date_to: date | None = Query(default=None, alias="date_to"),
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_CONSULTATIONS)),
    db: Session = Depends(get_db),
):
    slots = consultations_facade.get_available_slots(
        db,
        student_id=ctx.user_id,
        date_from=date_from,
        date_to=date_to,
    )
    return {"items": slots}


@router.get("/slots/{slot_id}/price")
def get_slot_price(
    slot_id: int,
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_CONSULTATIONS)),
    db: Session = Depends(get_db),
):
    try:
        return consultations_facade.get_price_quote(db, slot_id=slot_id)
    except DomainError as exc:
        translate_domain_error(exc)


@router.get("/my")
def get_my_bookings(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_CONSULTATIONS)),
    db: Session = Depends(get_db),
):
    rows = consultations_facade.get_my_bookings(db, student_id=ctx.user_id)
    return {
        "items": rows,
    }


@router.get("/invitations")
def get_invitations(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_CONSULTATIONS)),
    db: Session = Depends(get_db),
):
    invitations = consultations_facade.get_student_invitations(db, student_id=ctx.user_id)
    return {"items": [InvitationPayload(
        id=invitation.id,
        slot_id=invitation.slot_id,
        student_id=invitation.student_id,
        status=invitation.status,
        created_at=invitation.created_at,
        responded_at=invitation.responded_at,
    ).to_dict() for invitation in invitations]}


@router.get("/notifications")
def get_notifications(
    ctx: AccessContext = Depends(require_permission(Permission.VIEW_CONSULTATIONS)),
    db: Session = Depends(get_db),
):
    notifications = consultations_facade.get_student_notifications(db, student_id=ctx.user_id)
    return {"items": [NotificationPayload(
        id=notification.id,
        notification_type=notification.notification_type,
        title=notification.title,
        body=notification.body,
        invitation_id=notification.invitation_id,
        read_at=notification.read_at,
        created_at=notification.created_at,
    ).to_dict() for notification in notifications]}


@router.post("/slots/{slot_id}/book", status_code=201)
def book_slot(
    slot_id: int,
    ctx: AccessContext = Depends(require_student_consultation_booking()),
    db: Session = Depends(get_db),
):
    try:
        participant = consultations_facade.book_slot(db, student_id=ctx.user_id, slot_id=slot_id)
    except DomainError as exc:
        translate_domain_error(exc)
    return {
        "id": participant.id,
        "slot_id": participant.slot_id,
        "student_id": participant.student_id,
        "booking_status": participant.booking_status,
    }


@router.post("/bookings/{participant_id}/cancel")
def cancel_booking(
    participant_id: int,
    ctx: AccessContext = Depends(require_student_consultation_booking()),
    db: Session = Depends(get_db),
):
    try:
        participant = consultations_facade.cancel_booking(db, student_id=ctx.user_id, participant_id=participant_id)
    except DomainError as exc:
        translate_domain_error(exc)
    return {
        "id": participant.id,
        "booking_status": participant.booking_status,
        "cancelled_at": participant.cancelled_at.isoformat() if participant.cancelled_at else None,
    }


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: int,
    ctx: AccessContext = Depends(require_student_consultation_booking()),
    db: Session = Depends(get_db),
):
    try:
        participant = consultations_facade.accept_invitation(
            db,
            student_id=ctx.user_id,
            invitation_id=invitation_id,
        )
    except DomainError as exc:
        translate_domain_error(exc)

    return ParticipantPayload(
        id=participant.id,
        slot_id=participant.slot_id,
        student_id=participant.student_id,
        booking_status=participant.booking_status,
        source=participant.source,
    ).to_dict()


@router.post("/invitations/{invitation_id}/decline")
def decline_invitation(
    invitation_id: int,
    ctx: AccessContext = Depends(require_student_consultation_booking()),
    db: Session = Depends(get_db),
):
    try:
        invitation = consultations_facade.decline_invitation(
            db,
            student_id=ctx.user_id,
            invitation_id=invitation_id,
        )
    except DomainError as exc:
        translate_domain_error(exc)

    return InvitationPayload(
        id=invitation.id,
        slot_id=invitation.slot_id,
        student_id=invitation.student_id,
        status=invitation.status,
        created_at=invitation.created_at,
        responded_at=invitation.responded_at,
    ).to_dict()
