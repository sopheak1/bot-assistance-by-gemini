from dataclasses import dataclass

from lifesync.habits.domain.entities import Habit
from lifesync.habits.domain.repository import HabitRepository
from lifesync.habits.domain.value_objects import HabitType, Streak
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class CreateHabitRequest:
    chat_id: int
    name: str
    habit_type: str
    numeric_target: int | None = None
    numeric_unit: str | None = None


class CreateHabitUseCase:
    def __init__(self, repo: HabitRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: CreateHabitRequest) -> int:
        habit_type = HabitType(request.habit_type)
        habit = Habit(
            id=None,
            name=request.name,
            habit_type=habit_type,
            numeric_target=request.numeric_target,
            numeric_unit=request.numeric_unit,
            streak=Streak(0, 0),
            chat_id=ChatId(request.chat_id),
            created_at=self.clock.now(),
        )
        async with self.uow:
            saved = await self.repo.save(habit)
            await self.uow.commit()
            assert saved.id is not None
            return saved.id
