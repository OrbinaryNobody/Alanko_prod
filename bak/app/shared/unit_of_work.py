from __future__ import annotations

from typing import Any

from core.events import DomainEvent, EventBus


class UnitOfWork:
    def __init__(self, session: Any, event_bus: EventBus | None = None) -> None:
        self.session = session
        self.event_bus = event_bus
        self.events: list[DomainEvent] = []

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self.session.commit()
            if self.event_bus:
                for event in self.events:
                    self.event_bus.publish(event)
            return False

        self.session.rollback()
        return False
