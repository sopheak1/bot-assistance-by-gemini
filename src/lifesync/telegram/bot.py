from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from lifesync.config.settings import settings
from lifesync.telegram.fsm.sqlite_storage import SqliteFSMStorage
from lifesync.telegram.handlers import chat_setup, habits, projects, tasks
from lifesync.telegram.middleware.chat_context_middleware import ChatContextMiddleware
from lifesync.telegram.middleware.db_middleware import DatabaseMiddleware


def create_bot() -> Bot:
    session = None
    if settings.HTTP_PROXY:
        session = AiohttpSession(proxy=settings.HTTP_PROXY)
    return Bot(token=settings.BOT_TOKEN, session=session)


def create_dispatcher() -> Dispatcher:
    fsm_storage = SqliteFSMStorage(db_path=settings.BOT_DB_PATH)
    dp = Dispatcher(storage=fsm_storage)

    # Register global middlewares
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(ChatContextMiddleware())

    # Register routers
    dp.include_router(chat_setup.router)
    dp.include_router(projects.router)
    dp.include_router(tasks.router)
    dp.include_router(habits.router)

    return dp
