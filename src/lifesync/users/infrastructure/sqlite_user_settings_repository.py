from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from lifesync.users.domain.entities import UserSettings, Timezone, StandupHour, RolloverHour
from lifesync.users.domain.repository import UserSettingsRepository
from lifesync.persistence.models.bot_models import UserScheduleModel
from lifesync.shared_kernel.domain.value_objects import TelegramUserId

class SqliteUserSettingsRepository(UserSettingsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: TelegramUserId) -> UserSettings | None:
        stmt = select(UserScheduleModel).where(UserScheduleModel.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def save(self, settings: UserSettings) -> None:
        model = UserScheduleModel(
            telegram_id=settings.telegram_id,
            timezone=settings.timezone.value,
            standup_hour=settings.standup_hour.value,
            rollover_hour=settings.rollover_hour.value,
            created_at=settings.created_at
        )
        await self.session.merge(model)

    async def list_all(self) -> list[UserSettings]:
        stmt = select(UserScheduleModel)
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    def _map_to_domain(self, model: UserScheduleModel) -> UserSettings:
        return UserSettings(
            telegram_id=TelegramUserId(model.telegram_id),
            timezone=Timezone(model.timezone),
            standup_hour=StandupHour(model.standup_hour),
            rollover_hour=RolloverHour(model.rollover_hour),
            created_at=model.created_at
        )
