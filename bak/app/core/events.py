from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass(frozen=True)
class DomainEvent:
    pass


class EventBus:
    def __init__(self) -> None:
        self._subscribers: List[Callable[[DomainEvent], None]] = []

    def subscribe(self, handler: Callable[[DomainEvent], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._subscribers:
            handler(event)


event_bus = EventBus()
