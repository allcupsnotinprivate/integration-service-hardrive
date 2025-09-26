import abc

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeliveryEvent
from app.models.enums import DeliveryEventStatus
from app.repositories import ARepository
from app.utils.timestamps import now_with_tz


class ADeliveryEventsRepository(ARepository[DeliveryEvent, str], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DeliveryEvent)

    @abc.abstractmethod
    async def get_by_event_id(self, event_id: str) -> DeliveryEvent | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def enqueue(self, event: DeliveryEvent) -> DeliveryEvent:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_pending(self, *, limit: int) -> list[DeliveryEvent]:
        raise NotImplementedError

    @abc.abstractmethod
    async def mark_completed(self, event: DeliveryEvent) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def mark_failed(self, event: DeliveryEvent, *, error: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def increment_attempts(self, event: DeliveryEvent) -> None:
        raise NotImplementedError


class DeliveryEventsRepository(ADeliveryEventsRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_event_id(self, event_id: str) -> DeliveryEvent | None:
        stmt: Select[tuple[DeliveryEvent]] = select(self.model_class).filter_by(event_id=event_id)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def enqueue(self, event: DeliveryEvent) -> DeliveryEvent:
        await self.add(event)
        return event

    async def get_pending(self, *, limit: int) -> list[DeliveryEvent]:
        stmt: Select[tuple[DeliveryEvent]] = (
            select(self.model_class)
            .where(self.model_class.status.in_({DeliveryEventStatus.PENDING, DeliveryEventStatus.FAILED}))
            .order_by(self.model_class.available_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        events = list(result.scalars().all())
        for event in events:
            event.status = DeliveryEventStatus.PROCESSING
            event.updated_at = now_with_tz()
        return events

    async def mark_completed(self, event: DeliveryEvent) -> None:
        event.status = DeliveryEventStatus.COMPLETED
        event.updated_at = now_with_tz()
        event.last_error = None

    async def mark_failed(self, event: DeliveryEvent, *, error: str) -> None:
        event.status = DeliveryEventStatus.FAILED
        event.last_error = error
        event.updated_at = now_with_tz()

    async def increment_attempts(self, event: DeliveryEvent) -> None:
        event.attempts += 1
        event.updated_at = now_with_tz()
        if event.status == DeliveryEventStatus.PENDING:
            event.status = DeliveryEventStatus.PROCESSING
