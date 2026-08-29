from datetime import date, datetime, timedelta

from consultations.facade import consultations_facade
from consultations.timezone import CONSULTATION_TIMEZONE
from schedule.dtos import CalendarEventPayload
from education.facade import education_facade


class CalendarEventService:
    def list_events(
        self,
        db,
        *,
        date_from: date,
        date_to: date,
        teacher_id: int | None = None,
        event_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        if date_to < date_from:
            raise ValueError("date_to must not be before date_from")
        if event_type and event_type not in {"class", "consultation"}:
            return []

        events = []
        slots = consultations_facade.list_slots(
            db,
            date_from=date_from,
            date_to=date_to + timedelta(days=1),
        )
        occupied_slot_ids = consultations_facade.list_occupied_slot_ids(
            db,
            slot_ids=[slot.id for slot in slots],
        )
        for slot in slots:
            if slot.id not in occupied_slot_ids:
                continue
            if event_type and event_type != "consultation":
                continue
            if teacher_id is not None and slot.teacher_id != teacher_id:
                continue
            if status and slot.status != status:
                continue
            events.append(CalendarEventPayload(
                id=f"consultation-slot-{slot.id}",
                type="consultation",
                title="Индивидуальная консультация",
                start_at=slot.start_at,
                end_at=slot.end_at,
                status=slot.status,
                color="blue",
                teacher_id=slot.teacher_id,
                day_id=slot.day_id,
            ).to_dict())

        for schedule in education_facade.list_calendar_schedules(
            db,
            date_from=date_from,
            date_to=date_to,
        ):
            if event_type and event_type != "class":
                continue
            if status and status != "SCHEDULED":
                continue
            if teacher_id is not None and schedule.teacher_id != teacher_id:
                continue
            current_date = date_from + timedelta((schedule.weekday - date_from.weekday()) % 7)
            while current_date <= date_to:
                if current_date >= schedule.valid_from and (
                    schedule.valid_until is None or current_date <= schedule.valid_until
                ):
                    start_at = datetime.combine(current_date, schedule.start_time).replace(tzinfo=CONSULTATION_TIMEZONE)
                    end_at = datetime.combine(current_date, schedule.end_time).replace(tzinfo=CONSULTATION_TIMEZONE)
                    events.append(CalendarEventPayload(
                        id=f"group-schedule-{schedule.id}-{current_date.isoformat()}",
                        type="class",
                        title=schedule.group.title,
                        start_at=start_at,
                        end_at=end_at,
                        status="SCHEDULED",
                        color="green",
                        teacher_id=schedule.teacher_id,
                        day_id=None,
                    ).to_dict())
                current_date += timedelta(days=7)

        events.sort(key=lambda event: event["start_at"])
        return events

    def list_days(self, db, *, date_from: date, date_to: date) -> list[dict]:
        if date_to < date_from:
            raise ValueError("date_to must not be before date_from")
        days = consultations_facade.list_days(db, date_from=date_from, date_to=date_to)
        return [
            {
                "id": day.id,
                "date": day.date.isoformat(),
                "status": day.status,
                "available_from": day.available_from.isoformat() if day.available_from else None,
                "available_to": day.available_to.isoformat() if day.available_to else None,
            }
            for day in days
        ]


calendar_event_service = CalendarEventService()
