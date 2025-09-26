import abc
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SyncState
from app.repositories import ARepository


class ASyncStateRepository(ARepository[SyncState, str], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SyncState)

    @abc.abstractmethod
    async def get(self, key: str) -> SyncState | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def upsert(self, key: str, *, watermark: datetime | None, payload: dict | None = None) -> SyncState:
        raise NotImplementedError


class SyncStateRepository(ASyncStateRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get(self, key: str) -> SyncState | None:
        stmt: Select[tuple[SyncState]] = select(self.model_class).filter_by(key=key)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def upsert(self, key: str, *, watermark, payload: dict | None = None) -> SyncState:
        state = await self.get(key)
        if state is None:
            state = SyncState(key=key, watermark=watermark, payload=payload or {})
            await self.add(state)
        else:
            state.watermark = watermark
            if payload is not None:
                state.payload = payload
        return state
