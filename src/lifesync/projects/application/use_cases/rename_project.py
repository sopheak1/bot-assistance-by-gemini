from dataclasses import dataclass
from lifesync.projects.domain.repository import ProjectRepository
from lifesync.projects.domain.value_objects import ProjectName
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock

@dataclass
class RenameProjectRequest:
    project_id: int
    new_name: str

class RenameProjectUseCase:
    def __init__(self, repo: ProjectRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: RenameProjectRequest) -> None:
        project = await self.repo.get_by_id(request.project_id)
        if not project:
            raise ValueError("Project not found")

        project.rename(ProjectName(request.new_name), self.clock.now())
        async with self.uow:
            await self.repo.save(project)
            await self.uow.commit()
