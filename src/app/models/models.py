from datetime import datetime

from sqlalchemy import BIGINT, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.utils.timestamps import now_with_tz


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(BIGINT(), autoincrement=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), insert_default=now_with_tz, nullable=False)
