from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Returns the current timezone-aware datetime in UTC."""
        ...


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
