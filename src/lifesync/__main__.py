import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from aiogram import Bot
from lifesync.telegram.bot import create_bot, create_dispatcher
from lifesync.scheduling.infrastructure.apscheduler_adapter import APSchedulerAdapter
from lifesync.scheduling.application.use_cases.tick_handler import HourlyTickHandler
from lifesync.notifications.infrastructure.telegram_notifier import TelegramNotifier
from lifesync.users.infrastructure.sqlite_user_settings_repository import SqliteUserSettingsRepository
from lifesync.persistence.db import BotSessionLocal, init_bot_db
from lifesync.shared_kernel.domain.clock import SystemClock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickHandlerWrapper:
    def __init__(self, bot: Bot):
        self.notifier = TelegramNotifier(bot)
    
    async def handle_tick(self):
        async with BotSessionLocal() as bot_session:
            user_repo = SqliteUserSettingsRepository(bot_session)
            clock = SystemClock()
            handler = HourlyTickHandler(user_repo, clock, self.notifier)
            await handler.handle_tick()

def start_scheduler(bot: Bot) -> APSchedulerAdapter:
    scheduler = AsyncIOScheduler()
    wrapper = TickHandlerWrapper(bot)
    clock_tick_scheduler = APSchedulerAdapter(scheduler, wrapper)
    clock_tick_scheduler.start()
    return clock_tick_scheduler

async def main():
    bot = create_bot()
    dp = create_dispatcher()
    
    logger.info("Initializing database...")
    await init_bot_db()
    
    logger.info("Starting scheduler...")
    scheduler = start_scheduler(bot)
    
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
