from dataclasses import dataclass

from lifesync.projects.domain.repository import ProjectRepository
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class ProjectDTO:
    id: int
    name: str


class ListProjectsUseCase:
    def __init__(self, repo: ProjectRepository):
        self.repo = repo

    async def execute(self, chat_id: int) -> list[ProjectDTO]:
        projects = await self.repo.list_by_chat(ChatId(chat_id))
        return [
            ProjectDTO(
                id=p.id,  # type: ignore
                name=p.name.value,
            )
            for p in projects
        ]
