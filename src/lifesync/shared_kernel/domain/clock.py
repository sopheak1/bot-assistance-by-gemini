from typing import Protocol
from datetime import datetime, timezone

class Clock(Protocol):
    def now(self) -> datetime:
        """Returns the current timezone-aware datetime in UTC."""
        ...

class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
