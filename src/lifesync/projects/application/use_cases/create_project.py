from dataclasses import dataclass

from lifesync.projects.domain.entities import Project
from lifesync.projects.domain.repository import ProjectRepository
from lifesync.projects.domain.value_objects import ProjectName
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class CreateProjectRequest:
    chat_id: int
    name: str

class CreateProjectUseCase:
    def __init__(self, repo: ProjectRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: CreateProjectRequest) -> int:
        now = self.clock.now()
        project = Project(
            id=None,
            name=ProjectName(request.name),
            chat_id=ChatId(request.chat_id),
            created_at=now,
            updated_at=now
        )
        async with self.uow:
            saved = await self.repo.save(project)
            await self.uow.commit()
            return saved.id
