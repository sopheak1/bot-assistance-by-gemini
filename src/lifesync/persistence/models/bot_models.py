from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from lifesync.persistence.models.base import BotBase


class ChatBindingModel(BotBase):
    __tablename__ = "chat_bindings"

    chat_id: Mapped[int] = mapped_column(primary_key=True)
    owner_telegram_id: Mapped[int]
    domain_context: Mapped[str]
    bound_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserScheduleModel(BotBase):
    __tablename__ = "user_schedule"

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    timezone: Mapped[str] = mapped_column(default="Asia/Phnom_Penh")
    standup_hour: Mapped[int] = mapped_column(default=9)
    rollover_hour: Mapped[int] = mapped_column(default=2)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class QuoteModel(BotBase):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain_context: Mapped[str]
    sequence_index: Mapped[int]
    text: Mapped[str]
    author: Mapped[str | None]
