import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BOOLEAN, SMALLINT, TIMESTAMP, UUID, VARCHAR, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import DeliveryEventStatus, RecipientModule, UserRole
from app.utils.timestamps import now_with_tz

UserRoleT = ENUM(UserRole, name="user_role", create_type=False)
RecipientModuleT = ENUM(RecipientModule, name="recipient_module", create_type=False)
DeliveryEventStatusT = ENUM(DeliveryEventStatus, name="delivery_event_status", create_type=False)


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, insert_default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), insert_default=now_with_tz, nullable=False)


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(VARCHAR(52), nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(256), nullable=False, unique=True)
    fullname: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(BOOLEAN(), nullable=False, insert_default=True)
    role: Mapped[UserRole] = mapped_column(UserRoleT, nullable=False, insert_default=UserRole.OPERATOR)
    password_salt: Mapped[str] = mapped_column(VARCHAR(), nullable=False)
    password_hash: Mapped[str] = mapped_column(VARCHAR(), nullable=False)


class Recipient(Base):
    __tablename__ = "recipients"

    remote_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    module: Mapped[RecipientModule] = mapped_column(RecipientModuleT, nullable=False)
    name: Mapped[str | None] = mapped_column(VARCHAR(256), nullable=True)
    email: Mapped[str | None] = mapped_column(VARCHAR(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(BOOLEAN(), nullable=False, insert_default=True)
    router_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    remote_updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, insert_default=dict)

    __table_args__ = (UniqueConstraint("remote_id", "module", name="uq_recipient_remote"),)


class SyncState(Base):
    __tablename__ = "sync_state"

    key: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, unique=True)
    watermark: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)


class DocumentRecord(Base):
    __tablename__ = "document_records"

    external_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, unique=True)
    vtiger_id: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(256), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    remote_modified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class DocumentRecipientLink(Base):
    __tablename__ = "document_recipient_links"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
    )
    recipient_remote_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    recipient_module: Mapped[RecipientModule] = mapped_column(RecipientModuleT, nullable=False)
    relation_reference: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)

    __table_args__ = (
        UniqueConstraint("document_id", "recipient_remote_id", "recipient_module", name="uq_document_recipient"),
    )


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"

    event_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, unique=True)
    document_external_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False)
    status: Mapped[DeliveryEventStatus] = mapped_column(
        DeliveryEventStatusT, nullable=False, default=DeliveryEventStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(SMALLINT, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(VARCHAR(), nullable=True)
    available_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=now_with_tz)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=now_with_tz, onupdate=now_with_tz
    )

    __table_args__ = (Index("ix_delivery_events_status_available", "status", "available_at"),)