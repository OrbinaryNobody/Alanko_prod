from datetime import date

from sqlalchemy.orm import Session

from attendance.repositories.attendance_repository import attendance_repository
from core.exceptions import ConflictError, NotFoundError
from models.domains.attendance import Subscription
from shared.unit_of_work import UnitOfWork


class SubscriptionService:
    @staticmethod
    def _close_overlapping_active_subscriptions(db: Session, *, student_id: int, valid_from, valid_until):
        overlapping = (
            db.query(Subscription)
            .filter(
                Subscription.student_id == student_id,
                Subscription.status == "ACTIVE",
                Subscription.valid_from <= valid_until,
                Subscription.valid_until >= valid_from,
            )
            .all()
        )
        for subscription in overlapping:
            subscription.status = "CANCELLED"

    def list_all(self, db: Session):
        return db.query(Subscription).order_by(Subscription.created_at.desc(), Subscription.id.desc()).all()

    def update(self, db: Session, *, subscription_id: int, **data):
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise NotFoundError("Subscription not found")
        if data["valid_until"] < data["valid_from"]:
            raise ConflictError("Subscription end date must not precede start date")
        with UnitOfWork(db):
            for field, value in data.items():
                setattr(subscription, field, value)
            db.flush()
            db.refresh(subscription)
        return subscription

    def cancel(self, db: Session, *, subscription_id: int):
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise NotFoundError("Subscription not found")
        with UnitOfWork(db):
            subscription.status = "CANCELLED"
            db.flush()
        return subscription

    def renew(self, db: Session, *, subscription_id: int, valid_from: date | None = None, valid_until: date | None = None, extra_visits: int = 0, plan_name: str | None = None, payment_status: str | None = None, amount: int | None = None, currency: str | None = None):
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise NotFoundError("Subscription not found")
        if valid_until is None:
            valid_until = subscription.valid_until
        if valid_until < (valid_from or subscription.valid_from):
            raise ConflictError("Subscription end date must not precede start date")

        with UnitOfWork(db):
            if valid_from is not None:
                subscription.valid_from = valid_from
            subscription.valid_until = valid_until
            subscription.status = "ACTIVE"
            if plan_name:
                subscription.plan_name = plan_name
            if extra_visits > 0:
                subscription.total_visits += extra_visits
                subscription.remaining_visits += extra_visits
            if payment_status:
                subscription.payment_status = payment_status
            if amount is not None:
                subscription.amount = amount
            if currency:
                subscription.currency = currency
            db.flush()
            db.refresh(subscription)
        return subscription

    def create(self, db: Session, *, student_id: int, plan_name: str, total_visits: int, valid_from, valid_until, payment_status: str, amount: int, currency: str):
        if valid_until < valid_from:
            raise ConflictError("Subscription end date must not precede start date")
        with UnitOfWork(db):
            self._close_overlapping_active_subscriptions(db, student_id=student_id, valid_from=valid_from, valid_until=valid_until)
            subscription = Subscription(
                student_id=student_id,
                plan_name=plan_name,
                total_visits=total_visits,
                remaining_visits=total_visits,
                valid_from=valid_from,
                valid_until=valid_until,
                status="ACTIVE",
                payment_status=payment_status,
                amount=amount,
                currency=currency,
            )
            db.add(subscription)
            db.flush()
            db.refresh(subscription)
            return subscription

    def create_for_students(self, db: Session, *, student_ids: list[int], plan_name: str, total_visits: int, valid_from, valid_until, payment_status: str, amount: int, currency: str):
        if valid_until < valid_from:
            raise ConflictError("Subscription end date must not precede start date")
        if not student_ids:
            raise ConflictError("Group has no active students")

        with UnitOfWork(db):
            subscriptions = []
            for student_id in student_ids:
                self._close_overlapping_active_subscriptions(db, student_id=student_id, valid_from=valid_from, valid_until=valid_until)

                subscription = Subscription(
                    student_id=student_id,
                    plan_name=plan_name,
                    total_visits=total_visits,
                    remaining_visits=total_visits,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    status="ACTIVE",
                    payment_status=payment_status,
                    amount=amount,
                    currency=currency,
                )
                db.add(subscription)
                subscriptions.append(subscription)

            db.flush()
            for subscription in subscriptions:
                db.refresh(subscription)
            return subscriptions


subscription_service = SubscriptionService()