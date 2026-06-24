from dataclasses import dataclass
from datetime import date, timedelta

from lifesync.habits.domain.repository import HabitCheckInRepository, HabitRepository
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class HabitReportItem:
    habit_id: int
    name: str
    habit_type: str
    current_streak: int
    longest_streak: int
    checkins_last_7_days: int

class GetHabitReportUseCase:
    def __init__(self, habit_repo: HabitRepository, checkin_repo: HabitCheckInRepository):
        self.habit_repo = habit_repo
        self.checkin_repo = checkin_repo

    async def execute(self, chat_id: int, today: date) -> list[HabitReportItem]:
        habits = await self.habit_repo.list_by_chat(ChatId(chat_id))
        report = []
        start_date = today - timedelta(days=6)
        
        for habit in habits:
            checkins = await self.checkin_repo.list_by_habit_in_range(habit.id, start_date, today)
            report.append(HabitReportItem(
                habit_id=habit.id, # type: ignore
                name=habit.name,
                habit_type=habit.habit_type.value,
                current_streak=habit.streak.current,
                longest_streak=habit.streak.longest,
                checkins_last_7_days=len(checkins)
            ))
        return report
