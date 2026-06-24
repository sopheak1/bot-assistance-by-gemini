from dataclasses import dataclass
from datetime import datetime, date
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.habits.domain.value_objects import HabitType, Streak

@dataclass
class HabitCheckIn:
    id: int | None
    habit_id: int
    effective_date: date
    value_bool: bool | None
    value_numeric: int | None
    checked_at: datetime

@dataclass
class Habit:
    id: int | None
    name: str
    habit_type: HabitType
    numeric_target: int | None
    numeric_unit: str | None
    streak: Streak
    chat_id: ChatId
    created_at: datetime

    def update_streak(self, new_streak: Streak) -> None:
        self.streak = new_streak
