from dataclasses import dataclass
from datetime import datetime
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.projects.domain.value_objects import ProjectName

@dataclass
class Project:
    id: int | None
    name: ProjectName
    chat_id: ChatId
    created_at: datetime
    updated_at: datetime

    def rename(self, new_name: ProjectName, clock_now: datetime) -> None:
        self.name = new_name
        self.updated_at = clock_now
