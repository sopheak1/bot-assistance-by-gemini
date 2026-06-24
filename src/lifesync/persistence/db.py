import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from lifesync.config.settings import settings
import os

# Engine for bot.db
bot_engine = create_async_engine(f"sqlite+aiosqlite:///{settings.BOT_DB_PATH}", echo=(settings.ENVIRONMENT == "local"))
BotSessionLocal = async_sessionmaker(bind=bot_engine, class_=AsyncSession, expire_on_commit=False)

# Engines cache for user files
_user_engines: dict[int, async_sessionmaker[AsyncSession]] = {}

def _get_user_session_maker(telegram_id: int) -> async_sessionmaker[AsyncSession]:
    if telegram_id not in _user_engines:
        db_path = os.path.join(settings.USER_DB_DIR, f"{telegram_id}.db")
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=(settings.ENVIRONMENT == "local"))
        _user_engines[telegram_id] = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return _user_engines[telegram_id]

class BotDbRouter:
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with BotSessionLocal() as session:
            yield session

class UserFileRouter:
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id
        
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session_maker = _get_user_session_maker(self.telegram_id)
        async with session_maker() as session:
            yield session
