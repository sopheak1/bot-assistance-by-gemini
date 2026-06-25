from dataclasses import dataclass
from datetime import date

from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.tasks.domain.repository import TaskRepository
from lifesync.tasks.domain.value_objects import Deadline, ShortDescription, TaskStatus


@dataclass
class UpdateTaskRequest:
    task_id: int
    description: str | None = None
    status: str | None = None
    deadline: date | None = None


class UpdateTaskUseCase:
    def __init__(self, repo: TaskRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: UpdateTaskRequest) -> None:
        task = await self.repo.get_by_id(request.task_id)
        if not task:
            raise ValueError("Task not found")

        now = self.clock.now()

        if request.description is not None:
            task.description = ShortDescription(request.description)
            task.updated_at = now

        if request.deadline is not None:
            task.reschedule(Deadline(request.deadline), now)

        if request.status is not None:
            status = TaskStatus(request.status)
            if status == TaskStatus.DONE:
                task.mark_done(now)
            elif status == TaskStatus.IN_PROGRESS:
                task.mark_in_progress(now)
            else:
                task.mark_todo(now)

        async with self.uow:
            await self.repo.save(task)
            await self.uow.commit()
