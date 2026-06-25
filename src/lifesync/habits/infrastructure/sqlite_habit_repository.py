from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.habits.domain.entities import Habit, HabitCheckIn
from lifesync.habits.domain.repository import HabitCheckInRepository, HabitRepository
from lifesync.habits.domain.value_objects import HabitType, Streak
from lifesync.persistence.models.user_models import HabitCheckInModel, HabitModel
from lifesync.shared_kernel.domain.value_objects import ChatId


class SqliteHabitRepository(HabitRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, habit_id: int) -> Habit | None:
        stmt = select(HabitModel).where(HabitModel.id == habit_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def list_by_chat(self, chat_id: ChatId) -> list[Habit]:
        stmt = select(HabitModel).where(HabitModel.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    async def save(self, habit: Habit) -> Habit:
        if habit.id is None:
            model = HabitModel(
                chat_id=habit.chat_id,
                name=habit.name,
                habit_type=habit.habit_type.value,
                numeric_target=habit.numeric_target,
                numeric_unit=habit.numeric_unit,
                current_streak=habit.streak.current,
                longest_streak=habit.streak.longest,
                created_at=habit.created_at,
            )
            self.session.add(model)
            await self.session.flush()
            habit.id = model.id
        else:
            stmt = select(HabitModel).where(HabitModel.id == habit.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            model.name = habit.name
            model.habit_type = habit.habit_type.value
            model.numeric_target = habit.numeric_target
            model.numeric_unit = habit.numeric_unit
            model.current_streak = habit.streak.current
            model.longest_streak = habit.streak.longest
            await self.session.flush()
        return habit

    def _map_to_domain(self, model: HabitModel) -> Habit:
        return Habit(
            id=model.id,
            name=model.name,
            habit_type=HabitType(model.habit_type),
            numeric_target=model.numeric_target,
            numeric_unit=model.numeric_unit,
            streak=Streak(model.current_streak, model.longest_streak),
            chat_id=ChatId(model.chat_id),
            created_at=model.created_at,
        )


class SqliteHabitCheckInRepository(HabitCheckInRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_habit_and_date(
        self, habit_id: int, effective_date: date
    ) -> HabitCheckIn | None:
        stmt = select(HabitCheckInModel).where(
            HabitCheckInModel.habit_id == habit_id,
            HabitCheckInModel.effective_date == effective_date,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def get_last_checkin(self, habit_id: int) -> HabitCheckIn | None:
        stmt = (
            select(HabitCheckInModel)
            .where(HabitCheckInModel.habit_id == habit_id)
            .order_by(desc(HabitCheckInModel.effective_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def list_by_habit_in_range(
        self, habit_id: int, start: date, end: date
    ) -> list[HabitCheckIn]:
        stmt = select(HabitCheckInModel).where(
            HabitCheckInModel.habit_id == habit_id,
            HabitCheckInModel.effective_date >= start,
            HabitCheckInModel.effective_date <= end,
        )
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    async def save(self, checkin: HabitCheckIn) -> HabitCheckIn:
        if checkin.id is None:
            model = HabitCheckInModel(
                habit_id=checkin.habit_id,
                effective_date=checkin.effective_date,
                value_bool=checkin.value_bool,
                value_numeric=checkin.value_numeric,
                checked_at=checkin.checked_at,
            )
            self.session.add(model)
            await self.session.flush()
            checkin.id = model.id
        else:
            stmt = select(HabitCheckInModel).where(HabitCheckInModel.id == checkin.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            model.effective_date = checkin.effective_date
            model.value_bool = checkin.value_bool
            model.value_numeric = checkin.value_numeric
            model.checked_at = checkin.checked_at
            await self.session.flush()
        return checkin

    def _map_to_domain(self, model: HabitCheckInModel) -> HabitCheckIn:
        return HabitCheckIn(
            id=model.id,
            habit_id=model.habit_id,
            effective_date=model.effective_date,
            value_bool=model.value_bool,
            value_numeric=model.value_numeric,
            checked_at=model.checked_at,
        )
