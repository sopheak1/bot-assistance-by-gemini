from datetime import date

from sqlalchemy import Date, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.persistence.models.user_models import TaskModel
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.tasks.domain.entities import Task
from lifesync.tasks.domain.repository import TaskRepository
from lifesync.tasks.domain.value_objects import Deadline, ShortDescription, TaskStatus


class SqliteTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, task_id: int) -> Task | None:
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def list_by_project(self, project_id: int) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.project_id == project_id)
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    async def list_unfinished_before(self, chat_id: ChatId, d: date) -> list[Task]:
        stmt = select(TaskModel).where(
            TaskModel.chat_id == chat_id,
            TaskModel.status != TaskStatus.DONE.value,
            cast(TaskModel.created_at, Date) < d
        )
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    async def save(self, task: Task) -> Task:
        if task.id is None:
            model = TaskModel(
                chat_id=task.chat_id,
                project_id=task.project_id,
                description=task.description.value,
                status=task.status.value,
                deadline=task.deadline.value,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at
            )
            self.session.add(model)
            await self.session.flush()
            task.id = model.id
        else:
            stmt = select(TaskModel).where(TaskModel.id == task.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            model.description = task.description.value
            model.status = task.status.value
            model.deadline = task.deadline.value
            model.updated_at = task.updated_at
            model.completed_at = task.completed_at
            await self.session.flush()
        return task

    async def delete(self, task_id: int) -> None:
        stmt = delete(TaskModel).where(TaskModel.id == task_id)
        await self.session.execute(stmt)

    async def delete_by_project_id(self, project_id: int) -> None:
        stmt = delete(TaskModel).where(TaskModel.project_id == project_id)
        await self.session.execute(stmt)

    def _map_to_domain(self, model: TaskModel) -> Task:
        return Task(
            id=model.id,
            description=ShortDescription(model.description),
            status=TaskStatus(model.status),
            deadline=Deadline(model.deadline),
            project_id=model.project_id,
            chat_id=ChatId(model.chat_id),
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at
        )
