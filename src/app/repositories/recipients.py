import abc
from typing import Iterable

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recipient
from app.models.enums import RecipientModule
from app.repositories import ARepository
from app.utils.timestamps import now_with_tz


class ARecipientsRepository(ARepository[Recipient, str], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Recipient)

    @abc.abstractmethod
    async def get_by_remote(self, *, module: RecipientModule, remote_id: str) -> Recipient | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def upsert_many(self, records: Iterable[Recipient]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def deactivate_missing(self, *, module: RecipientModule, active_remote_ids: set[str]) -> int:
        raise NotImplementedError


class RecipientsRepository(ARecipientsRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_remote(self, *, module: RecipientModule, remote_id: str) -> Recipient | None:
        stmt: Select[tuple[Recipient]] = select(self.model_class).filter_by(module=module, remote_id=remote_id)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def upsert_many(self, records: Iterable[Recipient]) -> None:
        for record in records:
            existing = await self.get_by_remote(module=record.module, remote_id=record.remote_id)
            if existing:
                existing.name = record.name
                existing.email = record.email
                existing.phone = record.phone
                existing.is_active = record.is_active
                existing.router_agent_id = record.router_agent_id
                existing.remote_updated_at = record.remote_updated_at
                existing.meta = record.meta
            else:
                await self.add(record)

    async def deactivate_missing(self, *, module: RecipientModule, active_remote_ids: set[str]) -> int:
        if not active_remote_ids:
            stmt = (
                update(self.model_class)
                .where(self.model_class.module == module)
                .values(
                    is_active=False,
                    remote_updated_at=now_with_tz(),
                )
            )
        else:
            stmt = (
                update(self.model_class)
                .where(self.model_class.module == module, ~self.model_class.remote_id.in_(active_remote_ids))
                .values(is_active=False, remote_updated_at=now_with_tz())
            )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)
