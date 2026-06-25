import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import lifesync.persistence.models.bot_models  # noqa
import lifesync.persistence.models.user_models  # noqa
from lifesync.config.settings import settings
from lifesync.persistence.models.base import BotBase, UserBase

# Engine for bot.db
bot_engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.BOT_DB_PATH}", echo=(settings.ENVIRONMENT == "local")
)
BotSessionLocal = async_sessionmaker(bind=bot_engine, class_=AsyncSession, expire_on_commit=False)

# Engines cache for user files
_user_engines: dict[int, async_sessionmaker[AsyncSession]] = {}


async def get_user_session_maker(telegram_id: int) -> async_sessionmaker[AsyncSession]:
    if telegram_id not in _user_engines:
        db_path = os.path.join(settings.USER_DB_DIR, f"{telegram_id}.db")
        is_new = not os.path.exists(db_path)
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}", echo=(settings.ENVIRONMENT == "local")
        )
        if is_new:
            async with engine.begin() as conn:
                await conn.run_sync(UserBase.metadata.create_all)
        _user_engines[telegram_id] = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    return _user_engines[telegram_id]


async def init_bot_db() -> None:
    async with bot_engine.begin() as conn:
        await conn.run_sync(BotBase.metadata.create_all)


class BotDbRouter:
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with BotSessionLocal() as session:
            yield session


class UserFileRouter:
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session_maker = await get_user_session_maker(self.telegram_id)
        async with session_maker() as session:
            yield session
