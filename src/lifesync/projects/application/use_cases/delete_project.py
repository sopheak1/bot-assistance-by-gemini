from dataclasses import dataclass

from lifesync.projects.domain.repository import ProjectRepository
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.tasks.domain.repository import TaskRepository


@dataclass
class DeleteProjectRequest:
    project_id: int


class DeleteProjectUseCase:
    def __init__(self, project_repo: ProjectRepository, task_repo: TaskRepository, uow: UnitOfWork):
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.uow = uow

    async def execute(self, request: DeleteProjectRequest) -> None:
        async with self.uow:
            await self.task_repo.delete_by_project_id(request.project_id)
            await self.project_repo.delete(request.project_id)
            await self.uow.commit()
