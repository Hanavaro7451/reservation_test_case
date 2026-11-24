"""Enforce one active booking per slot."""

import sqlalchemy as sa
from alembic import op


revision = "7c3c59f7a8de"
down_revision = "2e5174a697d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_booking_active_slot",
        "booking",
        ["booking_date", "booking_time"],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index("uq_booking_active_slot", table_name="booking")
