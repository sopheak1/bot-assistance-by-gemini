from dataclasses import dataclass
from datetime import datetime

from lifesync.shared_kernel.domain.value_objects import ChatId, DomainContext, TelegramUserId


@dataclass
class ChatBinding:
    chat_id: ChatId
    domain_context: DomainContext
    bound_by: TelegramUserId
    bound_at: datetime
