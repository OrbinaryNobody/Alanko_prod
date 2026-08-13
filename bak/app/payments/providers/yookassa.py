from __future__ import annotations

from decimal import Decimal

from core.config import settings
from payments.providers.base import PaymentProvider


class YooKassaProvider(PaymentProvider):
    def create_payment(self, *, amount: Decimal, description: str, return_url: str, metadata: dict):
        return {
            "id": f"test-payment-{metadata.get('payment_id', 'unknown')}",
            "status": "pending",
            "confirmation_url": f"https://example.com/pay/test-payment-{metadata.get('payment_id', 'unknown')}",
            "amount": amount,
            "description": description,
            "return_url": return_url,
            "metadata": metadata,
        }

    def get_payment(self, payment_id: str):
        return {"id": payment_id, "status": "pending"}

    def refund_payment(self, payment_id: str, amount: Decimal | None = None):
        return {"id": payment_id, "status": "refunded"}

    def build_signature(self, *, payload: str) -> str:
        import hashlib
        import hmac

        secret = settings.yookassa_secret_key if hasattr(settings, "yookassa_secret_key") else ""
        return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
