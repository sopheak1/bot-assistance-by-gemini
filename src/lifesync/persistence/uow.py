from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lifesync.shared_kernel.application.unit_of_work import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
            
    async def commit(self) -> None:
        await self.session.commit()
        
    async def rollback(self) -> None:
        await self.session.rollback()
