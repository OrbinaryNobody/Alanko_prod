from __future__ import annotations

from fastapi import HTTPException


class DomainError(Exception):
    """Base class for domain-layer errors."""


class PermissionDenied(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class InvalidWebhookError(DomainError):
    pass


def to_http_exception(exc: DomainError) -> HTTPException:
    if isinstance(exc, PermissionDenied):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise HTTPException(status_code=400, detail=str(exc)) from exc
