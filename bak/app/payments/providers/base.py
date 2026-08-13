from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment(self, *, amount: Decimal, description: str, return_url: str, metadata: dict):
        raise NotImplementedError

    @abstractmethod
    def get_payment(self, payment_id: str):
        raise NotImplementedError

    @abstractmethod
    def refund_payment(self, payment_id: str, amount: Decimal | None = None):
        raise NotImplementedError

    def build_signature(self, *, payload: str) -> str:
        return payload

    def parse_webhook_event(self, *, payload: dict) -> tuple[str, str]:
        event_type = payload.get("event") or payload.get("type") or "unknown"
        status = payload.get("status") or payload.get("event_status") or "unknown"
        return event_type, status
