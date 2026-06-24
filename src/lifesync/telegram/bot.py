from aiogram import Bot, Dispatcher
from lifesync.config.settings import settings
from lifesync.telegram.middleware.db_middleware import DatabaseMiddleware
from lifesync.telegram.middleware.chat_context_middleware import ChatContextMiddleware
from lifesync.telegram.handlers import chat_setup, projects, tasks, habits

def create_bot() -> Bot:
    return Bot(token=settings.BOT_TOKEN)

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    
    # Register global middlewares
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(ChatContextMiddleware())
    
    # Register routers
    dp.include_router(chat_setup.router)
    dp.include_router(projects.router)
    dp.include_router(tasks.router)
    dp.include_router(habits.router)
    
    return dp
