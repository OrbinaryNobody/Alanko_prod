from sqlalchemy.orm import Session

from models.domains.education import Program
from models.domains.payments import Payment, SpecialOffer


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_offer_by_course_id(self, *, course_id: int) -> SpecialOffer | None:
        return (
            self.session.query(SpecialOffer)
            .filter(SpecialOffer.course_id == course_id)
            .filter(SpecialOffer.status.in_(["PUBLISHED", "REGISTRATION_OPEN"]))
            .order_by(SpecialOffer.created_at.desc())
            .first()
        )

    def get_active_offer_by_id(self, *, offer_id: int) -> SpecialOffer | None:
        return (
            self.session.query(SpecialOffer)
            .filter(SpecialOffer.id == offer_id)
            .filter(SpecialOffer.status.in_(["PUBLISHED", "REGISTRATION_OPEN"]))
            .one_or_none()
        )

    def create_payment(
        self,
        *,
        user_id: int,
        special_offer_id: int,
        amount: int,
        currency: str,
        provider: str,
        status: str,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            special_offer_id=special_offer_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status=status,
        )
        self.session.add(payment)
        self.session.flush()
        return payment

    def save(self, payment: Payment) -> Payment:
        self.session.add(payment)
        self.session.flush()
        return payment

    def get_payment_by_id(self, payment_id: int) -> Payment | None:
        return self.session.query(Payment).filter(Payment.id == payment_id).one_or_none()

    def get_payment_by_id_for_update(self, payment_id: int) -> Payment | None:
        return self.session.query(Payment).filter(Payment.id == payment_id).with_for_update().one_or_none()

    def get_offer_by_id(self, offer_id: int) -> SpecialOffer | None:
        return self.session.query(SpecialOffer).filter(SpecialOffer.id == offer_id).one_or_none()

    def get_course_by_id(self, course_id: int) -> Program | None:
        return self.session.query(Program).filter(Program.id == course_id).one_or_none()

    def get_payment_by_provider_id(self, *, provider_payment_id: str) -> Payment | None:
        return self.session.query(Payment).filter(Payment.provider_payment_id == provider_payment_id).one_or_none()

    def get_payment_by_provider_id_for_update(self, *, provider_payment_id: str) -> Payment | None:
        return (
            self.session.query(Payment)
            .filter(Payment.provider_payment_id == provider_payment_id)
            .with_for_update()
            .one_or_none()
        )

    def get_pending_payment_for_user_offer(self, *, user_id: int, special_offer_id: int) -> Payment | None:
        return (
            self.session.query(Payment)
            .filter(Payment.user_id == user_id)
            .filter(Payment.special_offer_id == special_offer_id)
            .filter(Payment.status == "PENDING")
            .order_by(Payment.id.desc())
            .first()
        )

