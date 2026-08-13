from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import DomainError, to_http_exception
from core.permissions import get_access_context
from db.database import get_db
from payments.facade import PaymentsFacade
from payments.schemas.payment import (
    CreateOfferPaymentRequest,
    CreateOfferPaymentResponse,
    CreateSpecialOfferPaymentRequest,
    PaymentStatusResponse,
    PaymentWebhookRequest,
)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/course", response_model=CreateOfferPaymentResponse)
def create_course_payment(
    data: CreateOfferPaymentRequest,
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    facade = PaymentsFacade(db)
    try:
        result = facade.create_course_payment(ctx=ctx, course_id=data.offer_id)
    except DomainError as exc:
        to_http_exception(exc)

    return CreateOfferPaymentResponse(**result)


@router.post("/special-offer", response_model=CreateOfferPaymentResponse)
def create_special_offer_payment(
    data: CreateSpecialOfferPaymentRequest,
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    facade = PaymentsFacade(db)
    try:
        result = facade.create_course_payment(ctx=ctx, course_id=data.offer_id)
    except DomainError as exc:
        to_http_exception(exc)

    return CreateOfferPaymentResponse(**result)


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
def get_payment_status(payment_id: int, ctx: AccessContext = Depends(get_access_context), db: Session = Depends(get_db)):
    facade = PaymentsFacade(db)
    try:
        result = facade.get_payment_status(payment_id)
    except DomainError as exc:
        to_http_exception(exc)

    return PaymentStatusResponse(**result)


@router.post("/{payment_id}/confirm", response_model=PaymentStatusResponse)
def confirm_payment(
    payment_id: int,
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    facade = PaymentsFacade(db)
    try:
        result = facade.confirm_payment(ctx=ctx, payment_id=payment_id)
    except DomainError as exc:
        to_http_exception(exc)

    return PaymentStatusResponse(**result)


@router.post("/webhook", response_model=PaymentStatusResponse)
def payment_webhook(data: PaymentWebhookRequest, db: Session = Depends(get_db)):
    facade = PaymentsFacade(db)
    try:
        result = facade.handle_webhook(
            provider_payment_id=data.provider_payment_id,
            signature=data.signature,
            payload=data.payload,
        )
    except DomainError as exc:
        to_http_exception(exc)

    return PaymentStatusResponse(**result)
