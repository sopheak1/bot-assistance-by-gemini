from dataclasses import dataclass
from enum import Enum


class HabitType(str, Enum):
    BINARY = "BINARY"
    NUMERIC = "NUMERIC"

@dataclass(frozen=True)
class Streak:
    current: int
    longest: int

    def __post_init__(self) -> None:
        if self.current < 0 or self.longest < 0:
            raise ValueError("Streak cannot be negative")
        if self.current > self.longest:
            raise ValueError("Current streak cannot exceed longest streak")

    def increment(self) -> "Streak":
        new_current = self.current + 1
        return Streak(new_current, max(new_current, self.longest))

    def reset(self) -> "Streak":
        return Streak(0, self.longest)
