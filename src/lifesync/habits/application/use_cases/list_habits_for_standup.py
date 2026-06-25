from dataclasses import dataclass
from datetime import date

from lifesync.habits.domain.repository import HabitCheckInRepository, HabitRepository
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class HabitStandupItem:
    habit_id: int
    name: str
    habit_type: str
    numeric_target: int | None
    numeric_unit: str | None
    checked_in_today: bool


class ListHabitsForStandupUseCase:
    def __init__(self, habit_repo: HabitRepository, checkin_repo: HabitCheckInRepository):
        self.habit_repo = habit_repo
        self.checkin_repo = checkin_repo

    async def execute(self, chat_id: int, effective_date: date) -> list[HabitStandupItem]:
        habits = await self.habit_repo.list_by_chat(ChatId(chat_id))
        result = []
        for habit in habits:
            assert habit.id is not None
            checkin = await self.checkin_repo.get_by_habit_and_date(habit.id, effective_date)
            result.append(
                HabitStandupItem(
                    habit_id=habit.id,
                    name=habit.name,
                    habit_type=habit.habit_type.value,
                    numeric_target=habit.numeric_target,
                    numeric_unit=habit.numeric_unit,
                    checked_in_today=checkin is not None,
                )
            )
        return result
