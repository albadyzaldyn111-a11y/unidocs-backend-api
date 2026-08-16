"""Add notification type for newly available files.

Revision ID: 20260816_01
Revises:
Create Date: 2026-08-16
"""

from alembic import op

revision = "20260816_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'NEW_FILE_AVAILABLE'")


def downgrade() -> None:
    # PostgreSQL does not safely support removing an enum value in place.
    pass
