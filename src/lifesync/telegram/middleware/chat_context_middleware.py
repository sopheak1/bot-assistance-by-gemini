from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from lifesync.chat_context.application.use_cases.resolve_chat_context import (
    ResolveChatContextUseCase,
)
from lifesync.chat_context.infrastructure.sqlite_chat_binding_repository import (
    SqliteChatBindingRepository,
)


class ChatContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        chat = data.get("event_chat")
        if not chat:
            return await handler(event, data)
            
        bot_session = data["bot_session"]
        repo = SqliteChatBindingRepository(bot_session)
        use_case = ResolveChatContextUseCase(repo)
        
        domain_context = await use_case.execute(chat.id)
        data["domain_context"] = domain_context
        
        return await handler(event, data)
