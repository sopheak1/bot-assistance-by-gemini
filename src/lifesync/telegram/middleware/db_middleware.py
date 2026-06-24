from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from lifesync.persistence.db import BotSessionLocal, get_user_session_maker


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        user_id = data["event_from_user"].id if "event_from_user" in data else None
        
        async with BotSessionLocal() as bot_session:
            data["bot_session"] = bot_session
            
            if user_id:
                user_session_maker = await get_user_session_maker(user_id)
                async with user_session_maker() as user_session:
                    data["user_session"] = user_session
                    return await handler(event, data)
            else:
                return await handler(event, data)
