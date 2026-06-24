from lifesync.quotes.domain.entities import Quote
from lifesync.quotes.domain.repository import QuoteProvider


class GetMotivationalQuoteUseCase:
    def __init__(self, provider: QuoteProvider):
        self.provider = provider

    async def execute(self) -> Quote:
        return await self.provider.get_random_quote()
