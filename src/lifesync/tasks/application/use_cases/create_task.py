from dataclasses import dataclass
from datetime import date
from lifesync.tasks.domain.repository import TaskRepository
from lifesync.tasks.domain.entities import Task
from lifesync.tasks.domain.value_objects import TaskStatus, ShortDescription, Deadline
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock

@dataclass
class CreateTaskRequest:
    chat_id: int
    project_id: int
    description: str
    deadline: date | None = None

class CreateTaskUseCase:
    def __init__(self, repo: TaskRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: CreateTaskRequest) -> int:
        now = self.clock.now()
        task = Task(
            id=None,
            description=ShortDescription(request.description),
            status=TaskStatus.TODO,
            deadline=Deadline(request.deadline),
            project_id=request.project_id,
            chat_id=ChatId(request.chat_id),
            created_at=now,
            updated_at=now,
            completed_at=None
        )
        async with self.uow:
            saved = await self.repo.save(task)
            await self.uow.commit()
            return saved.id
