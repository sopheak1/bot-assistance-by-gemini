from dataclasses import dataclass


@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""

    pass


class EventBus:
    """In-process event bus interface."""

    async def publish(self, event: DomainEvent) -> None:
        pass
