from dataclasses import dataclass
from datetime import date

from lifesync.tasks.domain.repository import TaskRepository


@dataclass
class TaskDTO:
    id: int
    project_id: int
    description: str
    status: str
    deadline: date | None

class ListTasksUseCase:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def execute(self, project_id: int) -> list[TaskDTO]:
        tasks = await self.repo.list_by_project(project_id)
        return [
            TaskDTO(
                id=t.id, # type: ignore
                project_id=t.project_id,
                description=t.description.value,
                status=t.status.value,
                deadline=t.deadline.value
            )
            for t in tasks
        ]
