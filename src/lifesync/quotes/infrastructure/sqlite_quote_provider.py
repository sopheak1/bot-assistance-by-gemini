from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from lifesync.persistence.models.bot_models import QuoteModel
from lifesync.quotes.domain.entities import Quote
from lifesync.quotes.domain.repository import QuoteProvider


class SqliteQuoteProvider(QuoteProvider):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_quote(self) -> Quote:
        stmt = select(QuoteModel).order_by(func.random()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            # Fallback if DB is empty
            return Quote(text="Keep pushing forward!", author="Life-Sync Bot")
        return Quote(text=model.text, author=model.author or "Unknown")
