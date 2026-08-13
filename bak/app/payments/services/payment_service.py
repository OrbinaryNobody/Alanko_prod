from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import json

from core.access import AccessContext
from core.config import settings
from core.exceptions import ConflictError, InvalidWebhookError, NotFoundError, PermissionDenied
from education.facade import EducationFacade
from payments.providers.yookassa import YooKassaProvider
from payments.repositories.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session: Session, education_facade: object | None = None):
        self.session = session
        self.repository = PaymentRepository(session)
        self.provider = YooKassaProvider()
        self.education_facade = education_facade or EducationFacade()

    def create_course_payment(self, *, ctx: AccessContext, course_id: int) -> dict:
        offer = self.repository.get_active_offer_by_course_id(course_id=course_id)
        if not offer:
            raise NotFoundError("OFFER_NOT_FOUND")
        return self._create_payment_for_offer(ctx=ctx, offer=offer)

    def create_offer_payment(self, *, ctx: AccessContext, offer_id: int) -> dict:
        offer = self.repository.get_offer_by_id(offer_id=offer_id)
        if not offer:
            raise NotFoundError("OFFER_NOT_FOUND")

        self._assert_offer_can_accept_registration(offer=offer)
        return self._create_payment_for_offer(ctx=ctx, offer=offer)

    def _create_payment_for_offer(self, *, ctx: AccessContext, offer: object) -> dict:
        if not self.repository.get_course_by_id(offer.course_id):
            raise NotFoundError("COURSE_NOT_FOUND")

        if self.education_facade.has_active_registration(self.session, ctx=ctx, course_id=offer.course_id):
            raise ConflictError("ALREADY_ENROLLED")

        existing_payment = self.repository.get_pending_payment_for_user_offer(
            user_id=ctx.user_id,
            special_offer_id=offer.id,
        )
        if existing_payment is not None:
            if not existing_payment.provider_payment_id:
                provider_result = self._create_provider_payment(payment=existing_payment, offer=offer)
                existing_payment.provider_payment_id = provider_result["id"]
                self.session.flush()
            return {
                "payment_id": existing_payment.id,
                "status": existing_payment.status,
                "payment_url": existing_payment.provider_payment_id,
            }

        try:
            payment = self.repository.create_payment(
                user_id=ctx.user_id,
                special_offer_id=offer.id,
                amount=offer.price,
                currency=offer.currency,
                provider="YOOKASSA",
                status="PENDING",
            )
            self.session.flush()
        except IntegrityError:
            self.session.rollback()
            existing_payment = self.repository.get_pending_payment_for_user_offer(
                user_id=ctx.user_id,
                special_offer_id=offer.id,
            )
            if existing_payment is not None:
                if not existing_payment.provider_payment_id:
                    provider_result = self._create_provider_payment(payment=existing_payment, offer=offer)
                    existing_payment.provider_payment_id = provider_result["id"]
                    self.session.flush()
                return {
                    "payment_id": existing_payment.id,
                    "status": existing_payment.status,
                    "payment_url": existing_payment.provider_payment_id,
                }
            raise

        provider_result = self._create_provider_payment(payment=payment, offer=offer)
        payment.provider_payment_id = provider_result["id"]
        self.session.flush()

        logger.info(
            "payment_created",
            extra={"payment_id": payment.id, "offer_id": offer.id, "course_id": offer.course_id, "user_id": ctx.user_id},
        )

        return {
            "payment_id": payment.id,
            "status": payment.status,
            "payment_url": provider_result.get("confirmation_url"),
        }

    def get_payment_status(self, payment_id: int) -> dict:
        payment = self.repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundError("PAYMENT_NOT_FOUND")

        return {"id": payment.id, "status": payment.status}

    def confirm_payment(self, *, ctx: AccessContext, payment_id: int) -> dict:
        payment = self.repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundError("PAYMENT_NOT_FOUND")
        if payment.user_id != ctx.user_id:
            raise PermissionDenied("FORBIDDEN")

        if payment.status == "PAID":
            return {"id": payment.id, "status": payment.status}

        self._mark_paid(payment=payment, user_id=ctx.user_id)
        return {"id": payment.id, "status": payment.status}

    def handle_webhook(self, *, provider_payment_id: str, signature: str | None = None, payload: str | None = None) -> dict:
        self._verify_webhook_signature(signature=signature, payload=payload)

        parsed_payload = self._parse_payload(payload=payload)
        self._validate_payload_matches_provider_id(provider_payment_id=provider_payment_id, payload=parsed_payload)
        event_type, event_status = self.provider.parse_webhook_event(payload=parsed_payload)
        if event_type not in {"payment.succeeded", "payment.canceled", "payment.failed", "payment.waiting_for_capture"}:
            raise InvalidWebhookError("INVALID_WEBHOOK")

        payment = self.repository.get_payment_by_provider_id_for_update(provider_payment_id=provider_payment_id)
        if not payment:
            raise NotFoundError("PAYMENT_NOT_FOUND")
        if payment.status == "PAID":
            return {"id": payment.id, "status": payment.status}

        success_event = event_status in {"succeeded", "paid", "success"} or event_type == "payment.succeeded"
        if success_event:
            self._mark_paid(payment=payment, user_id=payment.user_id)
            return {"id": payment.id, "status": payment.status}

        if event_status in {"canceled", "cancelled", "failed", "error"} or event_type in {"payment.canceled", "payment.failed"}:
            payment.status = "FAILED"
            payment.paid_at = None
            self.session.flush()
            return {"id": payment.id, "status": payment.status}

        if event_status in {"waiting_for_capture", "pending", "in_progress"} or event_type == "payment.waiting_for_capture":
            payment.status = "PENDING"
            self.session.flush()
            return {"id": payment.id, "status": payment.status}

        raise ConflictError("PAYMENT_NOT_PAID")

    def _assert_offer_can_accept_registration(self, *, offer: object) -> None:
        if offer.status not in {"PUBLISHED", "REGISTRATION_OPEN"}:
            if offer.status == "DRAFT":
                raise ConflictError("OFFER_NOT_PUBLISHED")
            if offer.status == "CANCELED":
                raise ConflictError("OFFER_CANCELED")
            if offer.status == "COMPLETED":
                raise ConflictError("OFFER_COMPLETED")
            if offer.status == "REGISTRATION_CLOSED":
                raise ConflictError("OFFER_REGISTRATION_CLOSED")
            raise ConflictError("OFFER_NOT_PUBLISHED")

        now = datetime.now(timezone.utc)
        if offer.registration_opens_at and offer.registration_opens_at > now:
            raise ConflictError("OFFER_REGISTRATION_CLOSED")
        if offer.registration_closes_at and offer.registration_closes_at < now:
            raise ConflictError("OFFER_REGISTRATION_CLOSED")

        if offer.starts_at and offer.starts_at > now:
            raise ConflictError("OFFER_NOT_STARTED")
        if offer.ends_at and offer.ends_at < now:
            raise ConflictError("OFFER_EXPIRED")

    def _mark_paid(self, *, payment: object, user_id: int) -> None:
        if getattr(payment, "status", None) == "PAID":
            return

        offer = self.repository.get_offer_by_id(payment.special_offer_id)
        if not offer:
            raise NotFoundError("OFFER_NOT_FOUND")

        self._assert_offer_can_accept_registration(offer=offer)

        self.education_facade.register_user_for_course(
            self.session,
            ctx=AccessContext.from_parts(user_id=user_id, roles=[], permissions=[], is_admin=False),
            course_id=offer.course_id,
            payment_id=payment.id,
        )

        payment.status = "PAID"
        payment.paid_at = datetime.now(timezone.utc)
        self.session.flush()

    def _create_provider_payment(self, *, payment: object, offer: object) -> dict:
        return self.provider.create_payment(
            amount=Decimal(str(payment.amount)),
            description=f"Payment for offer {offer.id}",
            return_url="https://example.com/payments/result",
            metadata={"payment_id": payment.id, "offer_id": offer.id},
        )

    def _verify_webhook_signature(self, *, signature: str | None, payload: str | None) -> None:
        if not signature or not payload:
            raise InvalidWebhookError("INVALID_WEBHOOK")

        if not settings.yookassa_secret_key:
            raise InvalidWebhookError("WEBHOOK_SECRET_MISSING")

        expected = self.provider.build_signature(payload=payload)
        if signature != expected:
            raise InvalidWebhookError("INVALID_WEBHOOK")

    def _validate_payload_matches_provider_id(self, *, provider_payment_id: str, payload: dict) -> None:
        candidate = (
            payload.get("provider_payment_id")
            or payload.get("payment_id")
            or payload.get("id")
            or (payload.get("object") or {}).get("id")
        )
        if candidate is not None and str(candidate) != str(provider_payment_id):
            raise InvalidWebhookError("PAYLOAD_PROVIDER_ID_MISMATCH")

    def _parse_payload(self, *, payload: str | None) -> dict:
        if not payload:
            return {}

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise InvalidWebhookError("INVALID_WEBHOOK") from exc
