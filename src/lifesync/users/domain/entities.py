from dataclasses import dataclass
from datetime import datetime

from lifesync.shared_kernel.domain.value_objects import TelegramUserId


@dataclass(frozen=True)
class Timezone:
    value: str

@dataclass(frozen=True)
class StandupHour:
    value: int # 0-23

@dataclass(frozen=True)
class RolloverHour:
    value: int # 0-23

@dataclass
class UserSettings:
    telegram_id: TelegramUserId
    timezone: Timezone
    standup_hour: StandupHour
    rollover_hour: RolloverHour
    created_at: datetime

    def update_timezone(self, tz: Timezone) -> None:
        self.timezone = tz

    def update_standup_hour(self, hour: StandupHour) -> None:
        self.standup_hour = hour

    def update_rollover_hour(self, hour: RolloverHour) -> None:
        self.rollover_hour = hour
