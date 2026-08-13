from __future__ import annotations

from sqlalchemy.orm import Session

from core.access import AccessContext
from payments.services.payment_service import PaymentService


class PaymentsFacade:
    def __init__(self, session: Session):
        self.session = session
        self.service = PaymentService(session)

    def create_course_payment(self, *, ctx: AccessContext, course_id: int) -> dict:
        return self.service.create_course_payment(ctx=ctx, course_id=course_id)

    def create_offer_payment(self, *, ctx: AccessContext, offer_id: int) -> dict:
        return self.service.create_offer_payment(ctx=ctx, offer_id=offer_id)

    def get_payment_status(self, payment_id: int) -> dict:
        return self.service.get_payment_status(payment_id)

    def confirm_payment(self, *, ctx: AccessContext, payment_id: int) -> dict:
        return self.service.confirm_payment(ctx=ctx, payment_id=payment_id)

    def handle_webhook(self, *, provider_payment_id: str, signature: str | None = None, payload: str | None = None) -> dict:
        return self.service.handle_webhook(
            provider_payment_id=provider_payment_id,
            signature=signature,
            payload=payload,
        )


payments_facade = PaymentsFacade
