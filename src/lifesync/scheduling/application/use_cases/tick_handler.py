import logging
import zoneinfo
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.chat_context.infrastructure.sqlite_chat_binding_repository import (
    SqliteChatBindingRepository,
)
from lifesync.habits.application.use_cases.list_habits_for_standup import (
    ListHabitsForStandupUseCase,
)
from lifesync.habits.infrastructure.sqlite_habit_repository import (
    SqliteHabitCheckInRepository,
    SqliteHabitRepository,
)
from lifesync.notifications.domain.ports import NotifierPort
from lifesync.persistence.db import get_user_session_maker
from lifesync.persistence.uow import SqlAlchemyUnitOfWork
from lifesync.quotes.application.use_cases.get_motivational_quote import GetMotivationalQuoteUseCase
from lifesync.quotes.infrastructure.sqlite_quote_provider import SqliteQuoteProvider
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.standup.application.use_cases.generate_standup import GenerateStandupUseCase
from lifesync.tasks.application.use_cases.list_unfinished_tasks import ListUnfinishedTasksUseCase
from lifesync.tasks.application.use_cases.rollover_unfinished_tasks import (
    RolloverTasksRequest,
    RolloverUnfinishedTasksUseCase,
)
from lifesync.tasks.domain.services import RolloverService
from lifesync.tasks.infrastructure.sqlite_task_repository import SqliteTaskRepository
from lifesync.users.domain.entities import UserSettings
from lifesync.users.domain.repository import UserSettingsRepository

logger = logging.getLogger(__name__)


class HourlyTickHandler:
    def __init__(
        self,
        bot_session: AsyncSession,
        user_repo: UserSettingsRepository,
        clock: Clock,
        notifier: NotifierPort,
    ):
        self.bot_session = bot_session
        self.user_repo = user_repo
        self.clock = clock
        self.notifier = notifier

    async def _process_user(self, user: UserSettings, now_utc: datetime) -> None:
        try:
            local_time = now_utc.astimezone(zoneinfo.ZoneInfo(user.timezone.value))
            current_hour = local_time.hour

            if current_hour == user.standup_hour.value:
                await self._trigger_standup(user, local_time)

            if current_hour == user.rollover_hour.value:
                await self._trigger_rollover(user, local_time)
        except Exception as e:
            logger.error(f"Error processing tick for user {user.telegram_id}: {e}")

    async def handle_tick(self) -> None:
        now_utc = self.clock.now()
        logger.info(f"Executing hourly tick at UTC: {now_utc}")

        users = await self.user_repo.list_all()

        import asyncio

        batch_size = 20
        for i in range(0, len(users), batch_size):
            batch = users[i : i + batch_size]
            tasks = [self._process_user(user, now_utc) for user in batch]
            await asyncio.gather(*tasks)

    async def _trigger_standup(self, user: UserSettings, local_time: datetime) -> None:
        logger.info(f"Triggering standup for user {user.telegram_id}")

        chat_repo = SqliteChatBindingRepository(self.bot_session)
        bindings = await chat_repo.list_by_owner(user.telegram_id)

        user_session_maker = await get_user_session_maker(user.telegram_id)

        for binding in bindings:
            async with user_session_maker() as user_session:
                task_repo = SqliteTaskRepository(user_session)
                habit_repo = SqliteHabitRepository(user_session)
                checkin_repo = SqliteHabitCheckInRepository(user_session)
                quote_provider = SqliteQuoteProvider(self.bot_session)

                list_tasks_uc = ListUnfinishedTasksUseCase(task_repo, self.clock)
                list_habits_uc = ListHabitsForStandupUseCase(habit_repo, checkin_repo)
                quote_uc = GetMotivationalQuoteUseCase(quote_provider)

                standup_uc = GenerateStandupUseCase(
                    chat_repo=chat_repo,
                    list_tasks_uc=list_tasks_uc,
                    list_habits_uc=list_habits_uc,
                    quote_uc=quote_uc,
                    clock=self.clock,
                )

                msg = await standup_uc.execute(binding.chat_id)
                if msg:
                    await self.notifier.send_message(
                        chat_id=msg.chat_id, text=msg.text, parse_mode="Markdown"
                    )

    async def _trigger_rollover(self, user: UserSettings, local_time: datetime) -> None:
        logger.info(f"Triggering rollover for user {user.telegram_id}")

        chat_repo = SqliteChatBindingRepository(self.bot_session)
        bindings = await chat_repo.list_by_owner(user.telegram_id)

        user_session_maker = await get_user_session_maker(user.telegram_id)

        for binding in bindings:
            if binding.domain_context.value == "WORK":
                async with user_session_maker() as user_session:
                    task_repo = SqliteTaskRepository(user_session)
                    uow = SqlAlchemyUnitOfWork(user_session)
                    rollover_svc = RolloverService()

                    rollover_uc = RolloverUnfinishedTasksUseCase(
                        task_repo, rollover_svc, uow, self.clock
                    )

                    req = RolloverTasksRequest(
                        chat_id=binding.chat_id, defer_ids=[], today=local_time.date()
                    )
                    await rollover_uc.execute(req)
                    await self.notifier.send_message(
                        chat_id=binding.chat_id,
                        text=(
                            "🔄 **Midnight Rollover Completed!**\n"
                            "Unfinished tasks have been moved to today."
                        ),
                        parse_mode="Markdown",
                    )
