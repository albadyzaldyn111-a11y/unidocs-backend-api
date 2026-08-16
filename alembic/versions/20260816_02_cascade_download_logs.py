"""Cascade download log cleanup when a file is deleted.

Revision ID: 20260816_02
Revises: 20260816_01
Create Date: 2026-08-16
"""

from alembic import op

revision = "20260816_02"
down_revision = "20260816_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE download_logs DROP CONSTRAINT IF EXISTS download_logs_file_id_fkey")
    op.execute(
        "ALTER TABLE download_logs ADD CONSTRAINT download_logs_file_id_fkey "
        "FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE download_logs DROP CONSTRAINT IF EXISTS download_logs_file_id_fkey")
    op.execute(
        "ALTER TABLE download_logs ADD CONSTRAINT download_logs_file_id_fkey "
        "FOREIGN KEY (file_id) REFERENCES files(id)"
    )
