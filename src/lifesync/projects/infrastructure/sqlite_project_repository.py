from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.persistence.models.user_models import ProjectModel
from lifesync.projects.domain.entities import Project
from lifesync.projects.domain.repository import ProjectRepository
from lifesync.projects.domain.value_objects import ProjectName
from lifesync.shared_kernel.domain.value_objects import ChatId


class SqliteProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, project_id: int) -> Project | None:
        stmt = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_domain(model)

    async def list_by_chat(self, chat_id: ChatId) -> list[Project]:
        stmt = select(ProjectModel).where(ProjectModel.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return [self._map_to_domain(m) for m in result.scalars().all()]

    async def save(self, project: Project) -> Project:
        if project.id is None:
            model = ProjectModel(
                chat_id=project.chat_id,
                name=project.name.value,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            self.session.add(model)
            await self.session.flush()
            project.id = model.id
        else:
            stmt = select(ProjectModel).where(ProjectModel.id == project.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            model.name = project.name.value
            model.updated_at = project.updated_at
            await self.session.flush()
        return project

    async def delete(self, project_id: int) -> None:
        stmt = delete(ProjectModel).where(ProjectModel.id == project_id)
        await self.session.execute(stmt)

    def _map_to_domain(self, model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=ProjectName(model.name),
            chat_id=ChatId(model.chat_id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
