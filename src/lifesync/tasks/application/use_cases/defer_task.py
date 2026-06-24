from dataclasses import dataclass
from datetime import date

from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.tasks.domain.repository import TaskRepository


@dataclass
class DeferTaskRequest:
    task_id: int
    new_date: date

class DeferTaskUseCase:
    def __init__(self, repo: TaskRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: DeferTaskRequest) -> None:
        task = await self.repo.get_by_id(request.task_id)
        if not task:
            raise ValueError("Task not found")
        
        task.defer_to(request.new_date, self.clock.now())
        async with self.uow:
            await self.repo.save(task)
            await self.uow.commit()
