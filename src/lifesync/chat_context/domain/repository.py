from typing import Protocol

from lifesync.chat_context.domain.entities import ChatBinding
from lifesync.shared_kernel.domain.value_objects import ChatId, TelegramUserId


class ChatBindingRepository(Protocol):
    async def get_by_chat_id(self, chat_id: ChatId) -> ChatBinding | None: ...
    async def list_by_owner(self, telegram_id: TelegramUserId) -> list[ChatBinding]: ...
    async def save(self, binding: ChatBinding) -> None: ...
