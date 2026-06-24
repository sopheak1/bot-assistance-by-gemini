from typing import Optional
from dataclasses import dataclass
from lifesync.users.domain.repository import UserSettingsRepository
from lifesync.shared_kernel.domain.value_objects import TelegramUserId

@dataclass
class UserSettingsDTO:
    telegram_id: int
    timezone: str
    standup_hour: int
    rollover_hour: int

class GetUserSettingsUseCase:
    def __init__(self, repo: UserSettingsRepository):
        self.repo = repo

    async def execute(self, telegram_id: int) -> Optional[UserSettingsDTO]:
        settings = await self.repo.get_by_telegram_id(TelegramUserId(telegram_id))
        if not settings:
            return None
        return UserSettingsDTO(
            telegram_id=settings.telegram_id,
            timezone=settings.timezone.value,
            standup_hour=settings.standup_hour.value,
            rollover_hour=settings.rollover_hour.value
        )
