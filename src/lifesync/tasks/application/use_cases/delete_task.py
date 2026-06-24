from dataclasses import dataclass

from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.tasks.domain.repository import TaskRepository


@dataclass
class DeleteTaskRequest:
    task_id: int

class DeleteTaskUseCase:
    def __init__(self, repo: TaskRepository, uow: UnitOfWork):
        self.repo = repo
        self.uow = uow

    async def execute(self, request: DeleteTaskRequest) -> None:
        async with self.uow:
            await self.repo.delete(request.task_id)
            await self.uow.commit()
