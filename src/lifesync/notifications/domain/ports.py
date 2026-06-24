from typing import Protocol


class NotifierPort(Protocol):
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
        ...
