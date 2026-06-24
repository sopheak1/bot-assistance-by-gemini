from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""
    pass

class EventBus:
    """In-process event bus interface."""
    async def publish(self, event: DomainEvent) -> None:
        pass
