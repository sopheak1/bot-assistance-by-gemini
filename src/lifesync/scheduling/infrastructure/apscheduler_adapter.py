import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

logger = logging.getLogger(__name__)

class APSchedulerAdapter:
    def __init__(self, scheduler: AsyncIOScheduler, tick_handler):
        self.scheduler = scheduler
        self.tick_handler = tick_handler

    def start(self):
        # Trigger at the top of every hour (minute=0, second=0)
        self.scheduler.add_job(
            self.tick_handler.handle_tick,
            CronTrigger(minute=0, second=0),
            id='hourly_clock_tick',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Scheduler started. Hourly tick scheduled.")
