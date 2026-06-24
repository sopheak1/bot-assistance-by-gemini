from dataclasses import dataclass
from datetime import date

from lifesync.habits.domain.entities import HabitCheckIn
from lifesync.habits.domain.repository import HabitCheckInRepository, HabitRepository
from lifesync.habits.domain.services import StreakCalculationService
from lifesync.habits.domain.value_objects import HabitType
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock


@dataclass
class CheckInHabitRequest:
    habit_id: int
    effective_date: date
    value_bool: bool | None = None
    value_numeric: int | None = None

class CheckInHabitUseCase:
    def __init__(
        self, 
        habit_repo: HabitRepository, 
        checkin_repo: HabitCheckInRepository, 
        streak_service: StreakCalculationService, 
        uow: UnitOfWork, 
        clock: Clock
    ):
        self.habit_repo = habit_repo
        self.checkin_repo = checkin_repo
        self.streak_service = streak_service
        self.uow = uow
        self.clock = clock

    async def execute(self, request: CheckInHabitRequest) -> None:
        habit = await self.habit_repo.get_by_id(request.habit_id)
        if not habit:
            raise ValueError("Habit not found")
            
        if habit.habit_type == HabitType.NUMERIC:
            if request.value_numeric is None:
                raise ValueError("Numeric value required for NUMERIC habit")
            if habit.numeric_target is not None and request.value_numeric < habit.numeric_target:
                raise ValueError(f"Value {request.value_numeric} does not meet target {habit.numeric_target}")
                
        existing = await self.checkin_repo.get_by_habit_and_date(habit.id, request.effective_date)
        if existing:
            return

        last_checkin = await self.checkin_repo.get_last_checkin(habit.id)
        
        checkin = HabitCheckIn(
            id=None,
            habit_id=habit.id,
            effective_date=request.effective_date,
            value_bool=request.value_bool,
            value_numeric=request.value_numeric,
            checked_at=self.clock.now()
        )
        
        new_streak = self.streak_service.compute_streak(habit, last_checkin, request.effective_date)
        habit.update_streak(new_streak)
        
        async with self.uow:
            await self.checkin_repo.save(checkin)
            await self.habit_repo.save(habit)
            await self.uow.commit()
