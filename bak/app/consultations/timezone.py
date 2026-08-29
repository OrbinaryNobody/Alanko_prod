from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.config import settings

CONSULTATION_TIMEZONE = ZoneInfo(settings.consultation_timezone)


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=CONSULTATION_TIMEZONE)
    return value.astimezone(timezone.utc)


def to_local(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(CONSULTATION_TIMEZONE)


def serialize_local(value: datetime | None) -> str | None:
    return to_local(value).isoformat() if value else None
