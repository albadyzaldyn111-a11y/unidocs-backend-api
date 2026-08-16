"""Align file metadata with the production schema.

Revision ID: 20260816_03
Revises: 20260816_02
Create Date: 2026-08-16
"""

from alembic import op

revision = "20260816_03"
down_revision = "20260816_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        "ALTER TABLE files ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE files ADD COLUMN IF NOT EXISTS mime_type VARCHAR(255)"
    )
    op.execute(
        "UPDATE files SET original_filename = COALESCE(NULLIF(original_filename, ''), title) "
        "WHERE original_filename IS NULL OR original_filename = ''"
    )
    op.execute(
        "UPDATE files SET mime_type = COALESCE(NULLIF(mime_type, ''), 'application/octet-stream') "
        "WHERE mime_type IS NULL OR mime_type = ''"
    )
    op.execute("ALTER TABLE files ALTER COLUMN original_filename SET NOT NULL")
    op.execute("ALTER TABLE files ALTER COLUMN mime_type SET NOT NULL")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE files DROP COLUMN IF EXISTS mime_type")
    op.execute("ALTER TABLE files DROP COLUMN IF EXISTS original_filename")
