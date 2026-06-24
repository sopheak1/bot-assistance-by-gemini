from dataclasses import dataclass

from lifesync.chat_context.domain.repository import ChatBindingRepository
from lifesync.shared_kernel.domain.value_objects import ChatId


@dataclass
class ChatContextDTO:
    domain_context: str
    owner_telegram_id: int

class ResolveChatContextUseCase:
    def __init__(self, repo: ChatBindingRepository):
        self.repo = repo

    async def execute(self, chat_id: int) -> ChatContextDTO | None:
        binding = await self.repo.get_by_chat_id(ChatId(chat_id))
        if not binding:
            return None
        return ChatContextDTO(
            domain_context=binding.domain_context.value,
            owner_telegram_id=binding.bound_by
        )
