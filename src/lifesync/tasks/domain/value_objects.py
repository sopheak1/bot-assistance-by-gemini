from dataclasses import dataclass
from enum import Enum
from datetime import date

class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

@dataclass(frozen=True)
class ShortDescription:
    value: str
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Task description cannot be empty")
        if len(self.value) > 200:
            raise ValueError("Task description is too long")

@dataclass(frozen=True)
class Deadline:
    value: date | None
