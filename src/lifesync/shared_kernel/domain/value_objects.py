from enum import Enum
from typing import NewType
from dataclasses import dataclass
from datetime import date

ChatId = NewType("ChatId", int)
TelegramUserId = NewType("TelegramUserId", int)

class DomainContext(str, Enum):
    WORK = "WORK"
    HABIT = "HABIT"

@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end
