from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.chat_context.domain.entities import ChatBinding
from lifesync.chat_context.domain.repository import ChatBindingRepository
from lifesync.persistence.models.bot_models import ChatBindingModel
from lifesync.shared_kernel.domain.value_objects import ChatId, DomainContext, TelegramUserId


class SqliteChatBindingRepository(ChatBindingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_chat_id(self, chat_id: ChatId) -> ChatBinding | None:
        stmt = select(ChatBindingModel).where(ChatBindingModel.chat_id == chat_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ChatBinding(
            chat_id=ChatId(model.chat_id),
            domain_context=DomainContext(model.domain_context),
            bound_by=TelegramUserId(model.owner_telegram_id),
            bound_at=model.bound_at,
        )

    async def list_by_owner(self, telegram_id: TelegramUserId) -> list[ChatBinding]:
        stmt = select(ChatBindingModel).where(ChatBindingModel.owner_telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [
            ChatBinding(
                chat_id=ChatId(m.chat_id),
                domain_context=DomainContext(m.domain_context),
                bound_by=TelegramUserId(m.owner_telegram_id),
                bound_at=m.bound_at,
            )
            for m in models
        ]

    async def save(self, binding: ChatBinding) -> None:
        model = ChatBindingModel(
            chat_id=binding.chat_id,
            owner_telegram_id=binding.bound_by,
            domain_context=binding.domain_context.value,
            bound_at=binding.bound_at,
        )
        await self.session.merge(model)
