import abc
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentRecipientLink, DocumentRecord
from app.models.enums import RecipientModule
from app.repositories import ARepository
from app.utils.timestamps import now_with_tz


class ADocumentRecordsRepository(ARepository[DocumentRecord, str], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentRecord)

    @abc.abstractmethod
    async def get_by_external_id(self, external_id: str) -> DocumentRecord | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def upsert(
        self,
        *,
        external_id: str,
        vtiger_id: str,
        name: str | None,
        content_hash: str | None,
        remote_modified_at: datetime | None,
    ) -> DocumentRecord:
        raise NotImplementedError


class DocumentRecordsRepository(ADocumentRecordsRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_external_id(self, external_id: str) -> DocumentRecord | None:
        stmt: Select[tuple[DocumentRecord]] = select(self.model_class).filter_by(external_id=external_id)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def upsert(
        self,
        *,
        external_id: str,
        vtiger_id: str,
        name: str | None,
        content_hash: str | None,
        remote_modified_at: datetime | None,
    ) -> DocumentRecord:
        record = await self.get_by_external_id(external_id)
        if record is None:
            record = DocumentRecord(
                external_id=external_id,
                vtiger_id=vtiger_id,
                name=name,
                content_hash=content_hash,
                remote_modified_at=remote_modified_at,
                last_processed_at=now_with_tz(),
            )
            await self.add(record)
        else:
            record.vtiger_id = vtiger_id
            record.name = name
            record.content_hash = content_hash
            record.remote_modified_at = remote_modified_at
            record.last_processed_at = now_with_tz()
        return record


class ADocumentRecipientLinksRepository(ARepository[DocumentRecipientLink, tuple[str, str]], abc.ABC):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentRecipientLink)

    @abc.abstractmethod
    async def exists(
        self,
        *,
        document_id: DocumentRecord,
        recipient_remote_id: str,
        recipient_module: RecipientModule,
    ) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def add_link(
        self,
        *,
        document_id: DocumentRecord,
        recipient_remote_id: str,
        recipient_module: RecipientModule,
        relation_reference: str | None,
    ) -> DocumentRecipientLink:
        raise NotImplementedError


class DocumentRecipientLinksRepository(ADocumentRecipientLinksRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def exists(
        self,
        *,
        document_id: DocumentRecord,
        recipient_remote_id: str,
        recipient_module: RecipientModule,
    ) -> bool:
        stmt: Select[tuple[DocumentRecipientLink]] = select(self.model_class).filter_by(
            document_id=document_id.id,
            recipient_remote_id=recipient_remote_id,
            recipient_module=recipient_module,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def add_link(
        self,
        *,
        document_id: DocumentRecord,
        recipient_remote_id: str,
        recipient_module: RecipientModule,
        relation_reference: str | None,
    ) -> DocumentRecipientLink:
        link = DocumentRecipientLink(
            document_id=document_id.id,
            recipient_remote_id=recipient_remote_id,
            recipient_module=recipient_module,
            relation_reference=relation_reference,
        )
        await self.add(link)
        return link
