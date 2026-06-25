import asyncio
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from lifesync.notifications.infrastructure.telegram_notifier import TelegramNotifier
from lifesync.persistence.db import BotSessionLocal, init_bot_db
from lifesync.scheduling.application.use_cases.tick_handler import HourlyTickHandler
from lifesync.scheduling.infrastructure.apscheduler_adapter import APSchedulerAdapter
from lifesync.shared_kernel.domain.clock import SystemClock
from lifesync.telegram.bot import create_bot, create_dispatcher
from lifesync.users.infrastructure.sqlite_user_settings_repository import (
    SqliteUserSettingsRepository,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TickHandlerWrapper:
    def __init__(self, bot: Bot):
        self.notifier = TelegramNotifier(bot)

    async def handle_tick(self) -> None:
        async with BotSessionLocal() as bot_session:
            user_repo = SqliteUserSettingsRepository(bot_session)
            clock = SystemClock()
            handler = HourlyTickHandler(bot_session, user_repo, clock, self.notifier)
            await handler.handle_tick()


def start_scheduler(bot: Bot) -> APSchedulerAdapter:
    scheduler = AsyncIOScheduler()
    wrapper = TickHandlerWrapper(bot)
    clock_tick_scheduler = APSchedulerAdapter(scheduler, wrapper)
    clock_tick_scheduler.start()
    return clock_tick_scheduler


async def main() -> None:
    bot = create_bot()
    dp = create_dispatcher()

    logger.info("Initializing database...")
    await init_bot_db()

    logger.info("Starting scheduler...")
    scheduler = start_scheduler(bot)

    logger.info("Starting bot...")
    try:
        while True:
            try:
                await dp.start_polling(bot, polling_timeout=10)
                break
            except Exception as e:
                logger.error(f"Polling crashed: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
    finally:
        scheduler.scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
