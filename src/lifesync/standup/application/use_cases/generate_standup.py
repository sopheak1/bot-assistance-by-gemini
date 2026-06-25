import logging
from dataclasses import dataclass

from lifesync.chat_context.domain.repository import ChatBindingRepository
from lifesync.habits.application.use_cases.list_habits_for_standup import (
    ListHabitsForStandupUseCase,
)
from lifesync.quotes.application.use_cases.get_motivational_quote import GetMotivationalQuoteUseCase
from lifesync.shared_kernel.domain.clock import Clock
from lifesync.shared_kernel.domain.value_objects import ChatId
from lifesync.tasks.application.use_cases.list_unfinished_tasks import ListUnfinishedTasksUseCase

logger = logging.getLogger(__name__)


@dataclass
class StandupMessage:
    chat_id: int
    text: str


class GenerateStandupUseCase:
    def __init__(
        self,
        chat_repo: ChatBindingRepository,
        list_tasks_uc: ListUnfinishedTasksUseCase,
        list_habits_uc: ListHabitsForStandupUseCase,
        quote_uc: GetMotivationalQuoteUseCase,
        clock: Clock,
    ):
        self.chat_repo = chat_repo
        self.list_tasks_uc = list_tasks_uc
        self.list_habits_uc = list_habits_uc
        self.quote_uc = quote_uc
        self.clock = clock

    async def execute(self, chat_id: int) -> StandupMessage | None:
        binding = await self.chat_repo.get_by_chat_id(ChatId(chat_id))
        if not binding:
            return None

        today = self.clock.now().date()
        quote = await self.quote_uc.execute()
        quote_text = f"\n\n💡 _{quote.text}_\n- {quote.author}"

        if binding.domain_context.value == "WORK":
            tasks = await self.list_tasks_uc.execute(chat_id)

            text = "🌅 **Good Morning! Here's your Work Standup:**\n\n"
            if not tasks:
                text += "You have no unfinished tasks. Enjoy your day!"
            else:
                for t in tasks:
                    text += f"🔸 {t.description}\n"
            text += quote_text
            return StandupMessage(chat_id=chat_id, text=text)

        elif binding.domain_context.value == "HABIT":
            habits = await self.list_habits_uc.execute(chat_id, today)
            text = "🌅 **Good Morning! Here's your Habit Standup:**\n\n"
            if not habits:
                text += "You don't have any habits tracked yet."
            else:
                for h in habits:
                    text += f"🔹 {h.name}\n"
            text += quote_text
            return StandupMessage(chat_id=chat_id, text=text)

        return None
