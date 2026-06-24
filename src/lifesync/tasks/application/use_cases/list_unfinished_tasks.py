from dataclasses import dataclass

from lifesync.shared_kernel.domain.clock import Clock
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.tasks.domain.repository import TaskRepository


@dataclass
class UnfinishedTaskDTO:
    id: int
    description: str

class ListUnfinishedTasksUseCase:
    def __init__(self, repo: TaskRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(self, chat_id: int) -> list[UnfinishedTaskDTO]:
        today = self.clock.now().date()
        tasks = await self.repo.list_unfinished_before(ChatId(chat_id), today)
        return [
            UnfinishedTaskDTO(
                id=t.id, # type: ignore
                description=t.description.value
            )
            for t in tasks
        ]
