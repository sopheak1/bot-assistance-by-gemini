from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from lifesync.chat_context.infrastructure.sqlite_chat_binding_repository import SqliteChatBindingRepository
from lifesync.chat_context.application.use_cases.resolve_chat_context import ResolveChatContextUseCase
from lifesync.shared_kernel.domain.value_objects import ChatId

class ChatContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
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
