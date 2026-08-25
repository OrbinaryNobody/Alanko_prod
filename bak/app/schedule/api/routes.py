from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from schedule.services.event_service import calendar_event_service
from core.access import AccessContext
from core.permissions import Permission, require_any_permission
from db.database import get_db

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _date_range(
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    start = date_from or date.today()
    end = date_to or (start + timedelta(days=6))
    if end < start:
        raise ValueError("date_to must not be before date_from")
    return start, end


@router.get("/events")
def list_events(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    teacher_id: int | None = Query(default=None, ge=1),
    event_type: str | None = Query(default=None, alias="type"),
    status: str | None = Query(default=None),
    ctx: AccessContext = Depends(require_any_permission(
        Permission.VIEW_CONSULTATIONS,
        Permission.MANAGE_CONSULTATIONS,
    )),
    db: Session = Depends(get_db),
):
    start, end = _date_range(date_from, date_to)
    return {
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "items": calendar_event_service.list_events(
            db,
            date_from=start,
            date_to=end,
            teacher_id=teacher_id,
            event_type=event_type,
            status=status,
        ),
    }


@router.get("/days")
def list_days(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    ctx: AccessContext = Depends(require_any_permission(
        Permission.VIEW_CONSULTATIONS,
        Permission.MANAGE_CONSULTATIONS,
    )),
    db: Session = Depends(get_db),
):
    start, end = _date_range(date_from, date_to)
    return {
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "items": calendar_event_service.list_days(db, date_from=start, date_to=end),
    }
