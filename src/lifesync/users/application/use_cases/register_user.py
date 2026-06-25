from dataclasses import dataclass

from lifesync.config.settings import settings
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.shared_kernel.domain.value_objects import TelegramUserId
from lifesync.users.domain.entities import RolloverHour, StandupHour, Timezone, UserSettings
from lifesync.users.domain.repository import UserSettingsRepository


@dataclass
class RegisterUserRequest:
    telegram_id: int


class RegisterUserUseCase:
    def __init__(self, repo: UserSettingsRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: RegisterUserRequest) -> None:
        user_id = TelegramUserId(request.telegram_id)
        existing = await self.repo.get_by_telegram_id(user_id)
        if existing:
            return

        user_settings = UserSettings(
            telegram_id=user_id,
            timezone=Timezone(settings.DEFAULT_TIMEZONE),
            standup_hour=StandupHour(settings.DEFAULT_STANDUP_HOUR),
            rollover_hour=RolloverHour(settings.DEFAULT_ROLLOVER_HOUR),
            created_at=self.clock.now(),
        )
        async with self.uow:
            await self.repo.save(user_settings)
            await self.uow.commit()
