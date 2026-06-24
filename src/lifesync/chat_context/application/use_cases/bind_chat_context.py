from dataclasses import dataclass
from lifesync.shared_kernel.domain.value_objects import ChatId, TelegramUserId, DomainContext
from lifesync.chat_context.domain.entities import ChatBinding
from lifesync.chat_context.domain.repository import ChatBindingRepository
from lifesync.shared_kernel.application.unit_of_work import UnitOfWork
from lifesync.shared_kernel.domain.clock import Clock

@dataclass
class BindChatContextRequest:
    chat_id: int
    telegram_id: int
    domain_context: str

class BindChatContextUseCase:
    def __init__(self, repo: ChatBindingRepository, uow: UnitOfWork, clock: Clock):
        self.repo = repo
        self.uow = uow
        self.clock = clock

    async def execute(self, request: BindChatContextRequest) -> None:
        binding = ChatBinding(
            chat_id=ChatId(request.chat_id),
            bound_by=TelegramUserId(request.telegram_id),
            domain_context=DomainContext(request.domain_context),
            bound_at=self.clock.now()
        )
        async with self.uow:
            await self.repo.save(binding)
            await self.uow.commit()
