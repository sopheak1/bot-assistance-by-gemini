from dataclasses import dataclass
from lifesync.users.domain.repository import UserSettingsRepository
from lifesync.shared_kernel.domain.value_objects import TelegramUserId
from lifesync.users.domain.entities import Timezone, StandupHour, RolloverHour
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork

@dataclass
class UpdateSettingsRequest:
    telegram_id: int
    timezone: str | None = None
    standup_hour: int | None = None
    rollover_hour: int | None = None

class UpdateSettingsUseCase:
    def __init__(self, repo: UserSettingsRepository, uow: UnitOfWork):
        self.repo = repo
        self.uow = uow

    async def execute(self, request: UpdateSettingsRequest) -> None:
        settings = await self.repo.get_by_telegram_id(TelegramUserId(request.telegram_id))
        if not settings:
            raise ValueError("User settings not found")
        
        if request.timezone is not None:
            settings.update_timezone(Timezone(request.timezone))
        if request.standup_hour is not None:
            settings.update_standup_hour(StandupHour(request.standup_hour))
        if request.rollover_hour is not None:
            settings.update_rollover_hour(RolloverHour(request.rollover_hour))
            
        async with self.uow:
            await self.repo.save(settings)
            await self.uow.commit()
