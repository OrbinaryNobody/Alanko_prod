from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.access import AccessContext
from core.config import settings
from core.exceptions import ConflictError, NotFoundError
from models.base import Base
from models.domains.education import Program
from models.domains.payments import Payment, SpecialOffer
from payments.services.payment_service import PaymentService

settings.yookassa_secret_key = "test-secret"


def _make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_flush=False)
    return Session()


def test_create_course_payment_uses_active_special_offer():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="REGISTRATION_OPEN")
    session.add(offer)
    session.commit()

    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)
    result = service.create_course_payment(ctx=ctx, course_id=7)

    payment = session.query(Payment).one()

    assert result["payment_id"] == payment.id
    assert result["status"] == "PENDING"
    assert payment.special_offer_id == offer.id
    assert payment.amount == 1500
    assert payment.currency == "RUB"


def test_create_offer_payment_uses_offer_id_as_primary_entrypoint():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="REGISTRATION_OPEN")
    session.add(offer)
    session.commit()

    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)
    result = service.create_offer_payment(ctx=ctx, offer_id=offer.id)

    payment = session.query(Payment).one()

    assert result["payment_id"] == payment.id
    assert payment.special_offer_id == offer.id
    assert payment.amount == 1500


def test_create_offer_payment_rejects_draft_offer():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="DRAFT")
    session.add(offer)
    session.commit()

    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)

    try:
        service.create_offer_payment(ctx=ctx, offer_id=offer.id)
    except ConflictError as exc:
        assert str(exc) == "OFFER_NOT_PUBLISHED"
    else:
        raise AssertionError("Expected ConflictError")


def test_create_offer_payment_rejects_closed_registration_window():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(
        course_id=7,
        price=1500,
        currency="RUB",
        status="REGISTRATION_OPEN",
        registration_opens_at=datetime.now(timezone.utc) - timedelta(days=2),
        registration_closes_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    session.add(offer)
    session.commit()

    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)

    try:
        service.create_offer_payment(ctx=ctx, offer_id=offer.id)
    except ConflictError as exc:
        assert str(exc) == "OFFER_REGISTRATION_CLOSED"
    else:
        raise AssertionError("Expected ConflictError")


def test_create_course_payment_requires_active_offer():
    session = _make_session()
    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)

    try:
        service.create_course_payment(ctx=ctx, course_id=999)
    except NotFoundError as exc:
        assert str(exc) == "OFFER_NOT_FOUND"
    else:
        raise AssertionError("Expected NotFoundError")


def test_create_offer_payment_reuses_existing_pending_payment():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="REGISTRATION_OPEN")
    session.add(offer)
    session.commit()

    service = PaymentService(session)
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)

    result_one = service.create_offer_payment(ctx=ctx, offer_id=offer.id)
    result_two = service.create_offer_payment(ctx=ctx, offer_id=offer.id)

    assert result_one["payment_id"] == result_two["payment_id"]
    assert len(session.query(Payment).all()) == 1


def test_handle_webhook_is_idempotent_for_duplicate_successful_webhooks():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="REGISTRATION_OPEN")
    session.add(offer)
    payment = Payment(
        user_id=1,
        special_offer_id=offer.id,
        amount=1500,
        currency="RUB",
        provider="YOOKASSA",
        status="PENDING",
        provider_payment_id="provider-duplicate",
    )
    session.add(payment)
    session.commit()

    calls = []

    class FakeEducationFacade:
        def register_user_for_course(self, db, *, ctx, course_id, payment_id):
            calls.append((ctx.user_id, course_id, payment_id))
            return {"status": "registered"}

    service = PaymentService(session, education_facade=FakeEducationFacade())

    payload = '{"event":"payment.succeeded", "id":"provider-duplicate"}'
    signature = service.provider.build_signature(payload=payload)

    first = service.handle_webhook(provider_payment_id="provider-duplicate", signature=signature, payload=payload)
    second = service.handle_webhook(provider_payment_id="provider-duplicate", signature=signature, payload=payload)

    assert first == {"id": payment.id, "status": "PAID"}
    assert second == {"id": payment.id, "status": "PAID"}
    assert calls == [(1, 7, payment.id)]


def test_mark_paid_delegates_course_registration_to_education_facade():
    session = _make_session()
    session.add(Program(id=7, title="Test course", description="Test"))
    offer = SpecialOffer(course_id=7, price=1500, currency="RUB", status="REGISTRATION_OPEN")
    session.add(offer)
    payment = Payment(
        user_id=1,
        special_offer_id=offer.id,
        amount=1500,
        currency="RUB",
        provider="YOOKASSA",
        status="PENDING",
    )
    session.add(payment)
    session.commit()

    calls = []

    class FakeEducationFacade:
        def register_user_for_course(self, db, *, ctx, course_id, payment_id):
            calls.append((ctx.user_id, course_id, payment_id))
            return {"status": "registered"}

    service = PaymentService(session, education_facade=FakeEducationFacade())
    ctx = AccessContext.from_parts(user_id=1, roles=[], permissions=[], is_admin=False)

    service._mark_paid(payment=payment, user_id=ctx.user_id)

    assert calls == [(1, 7, payment.id)]
    assert payment.status == "PAID"


def test_handle_webhook_is_idempotent_for_already_paid_payment():
    session = _make_session()
    payment = Payment(
        user_id=1,
        special_offer_id=1,
        amount=1500,
        currency="RUB",
        provider="YOOKASSA",
        status="PAID",
        provider_payment_id="provider-1",
    )
    session.add(payment)
    session.commit()

    service = PaymentService(session)
    payload = '{"event":"payment.succeeded"}'
    signature = service.provider.build_signature(payload=payload)

    result = service.handle_webhook(
        provider_payment_id="provider-1",
        signature=signature,
        payload=payload,
    )

    assert result == {"id": payment.id, "status": "PAID"}


def test_handle_webhook_marks_failed_payment_when_provider_reports_failure():
    session = _make_session()
    payment = Payment(
        user_id=1,
        special_offer_id=1,
        amount=1500,
        currency="RUB",
        provider="YOOKASSA",
        status="PENDING",
        provider_payment_id="provider-2",
    )
    session.add(payment)
    session.commit()

    service = PaymentService(session)
    payload = '{"event":"payment.failed"}'
    signature = service.provider.build_signature(payload=payload)

    result = service.handle_webhook(
        provider_payment_id="provider-2",
        signature=signature,
        payload=payload,
    )

    assert result == {"id": payment.id, "status": "FAILED"}
    assert payment.status == "FAILED"


def test_handle_webhook_keeps_payment_pending_for_waiting_for_capture():
    session = _make_session()
    payment = Payment(
        user_id=1,
        special_offer_id=1,
        amount=1500,
        currency="RUB",
        provider="YOOKASSA",
        status="PENDING",
        provider_payment_id="provider-3",
    )
    session.add(payment)
    session.commit()

    service = PaymentService(session)
    payload = '{"event":"payment.waiting_for_capture"}'
    signature = service.provider.build_signature(payload=payload)

    result = service.handle_webhook(
        provider_payment_id="provider-3",
        signature=signature,
        payload=payload,
    )

    assert result == {"id": payment.id, "status": "PENDING"}
    assert payment.status == "PENDING"
