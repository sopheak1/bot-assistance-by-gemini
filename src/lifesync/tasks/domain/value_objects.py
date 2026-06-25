from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass(frozen=True)
class ShortDescription:
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Task description cannot be empty")
        if len(self.value) > 200:
            raise ValueError("Task description is too long")


@dataclass(frozen=True)
class Deadline:
    value: date | None
