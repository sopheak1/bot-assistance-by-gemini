from aiogram import Bot

from lifesync.notifications.domain.ports import NotifierPort


class TelegramNotifier(NotifierPort):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
        await self.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
