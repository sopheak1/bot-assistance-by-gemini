from typing import Protocol

from lifesync.quotes.domain.entities import Quote


class QuoteProvider(Protocol):
    async def get_random_quote(self) -> Quote: ...
