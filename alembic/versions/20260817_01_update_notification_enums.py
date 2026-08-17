"""Update notification enums for role and status changes.

Revision ID: 20260817_01
Revises: 20260816_03
Create Date: 2026-08-17
"""

from alembic import op

revision = "20260817_01"
down_revision = "20260816_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Add missing enum values to notificationtype
    new_values = [
        "file_approved",
        "file_rejected",
        "upload_request_approved",
        "upload_request_rejected",
        "new_version_approved",
        "role_changed",
        "account_status_changed",
    ]
    
    for val in new_values:
        op.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{val}'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type easily.
    pass
