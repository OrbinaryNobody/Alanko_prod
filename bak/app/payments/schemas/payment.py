from pydantic import BaseModel, Field


class CreateOfferPaymentRequest(BaseModel):
    offer_id: int = Field(..., ge=1)


class CreateSpecialOfferPaymentRequest(BaseModel):
    offer_id: int = Field(..., ge=1)


class CreateOfferPaymentResponse(BaseModel):
    payment_id: int
    status: str
    payment_url: str | None = None


class PaymentStatusResponse(BaseModel):
    id: int
    status: str


class PaymentWebhookRequest(BaseModel):
    provider_payment_id: str
    signature: str | None = None
    payload: str | None = None
