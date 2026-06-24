import zoneinfo
from datetime import date, datetime, timedelta

from lifesync.habits.domain.entities import Habit, HabitCheckIn
from lifesync.habits.domain.value_objects import Streak
from lifesync.users.domain.entities import RolloverHour, Timezone


class HabitDateService:
    @staticmethod
    def get_effective_date(clock_now: datetime, tz: Timezone, rollover: RolloverHour) -> date:
        local_time = clock_now.astimezone(zoneinfo.ZoneInfo(tz.value))
        if local_time.hour < rollover.value:
            return (local_time - timedelta(days=1)).date()
        return local_time.date()

class StreakCalculationService:
    @staticmethod
    def compute_streak(habit: Habit, last_checkin: HabitCheckIn | None, effective_date: date) -> Streak:
        if not last_checkin:
            return habit.streak.increment()
            
        diff = (effective_date - last_checkin.effective_date).days
        
        if diff <= 0:
            return habit.streak
        elif diff == 1:
            return habit.streak.increment()
        else:
            return habit.streak.reset().increment()
