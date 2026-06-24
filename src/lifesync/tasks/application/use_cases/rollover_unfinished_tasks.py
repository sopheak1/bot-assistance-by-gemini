from dataclasses import dataclass
from datetime import date
from lifesync.tasks.domain.repository import TaskRepository
from lifesync.tasks.domain.services import RolloverService
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock

@dataclass
class RolloverTasksRequest:
    chat_id: int
    defer_ids: list[int]
    today: date

class RolloverUnfinishedTasksUseCase:
    def __init__(self, repo: TaskRepository, rollover_service: RolloverService, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.rollover_service = rollover_service
        self.uow = uow
        self.clock = clock

    async def execute(self, request: RolloverTasksRequest) -> None:
        tasks = await self.repo.list_unfinished_before(ChatId(request.chat_id), request.today)
        
        self.rollover_service.rollover(tasks, request.today, request.defer_ids)
        
        async with self.uow:
            for t in tasks:
                t.updated_at = self.clock.now()
                await self.repo.save(t)
            await self.uow.commit()
