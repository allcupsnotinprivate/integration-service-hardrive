import uuid
from datetime import datetime

from sqlalchemy import BOOLEAN, TIMESTAMP, UUID, VARCHAR
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import UserRole
from app.utils.timestamps import now_with_tz

UserRoleT = ENUM(UserRole, name="user_role", create_type=False)


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
