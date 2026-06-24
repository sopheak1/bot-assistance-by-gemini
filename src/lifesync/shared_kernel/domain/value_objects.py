from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import NewType

ChatId = NewType("ChatId", int)
TelegramUserId = NewType("TelegramUserId", int)

class DomainContext(StrEnum):
    WORK = "WORK"
    HABIT = "HABIT"

@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end
