"""init

Revision ID: 2f30b9dfae15
Revises:
Create Date: 2025-09-16 01:59:32.743472

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "2f30b9dfae15"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UserRoleEnum = postgresql.ENUM("SYSTEM", "OPERATOR", name="user_role", create_type=False)


def upgrade() -> None:
    UserRoleEnum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("username", sa.VARCHAR(length=52), nullable=False),
        sa.Column("email", sa.VARCHAR(length=256), nullable=False),
        sa.Column("fullname", sa.VARCHAR(length=128), nullable=True),
        sa.Column("is_active", sa.BOOLEAN(), nullable=False),
        sa.Column("role", UserRoleEnum, nullable=False),
        sa.Column("password_salt", sa.VARCHAR(), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )


def downgrade() -> None:
    op.drop_table("users")
    UserRoleEnum.drop(op.get_bind(), checkfirst=True)
