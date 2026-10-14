"""Add shared sliding-window rate limit buckets."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c8a1d3e6f902"
down_revision = "1493b09f19f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_buckets",
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.DateTime(timezone=True)), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_rate_limit_buckets")),
    )
    op.create_index(
        op.f("ix_rate_limit_buckets_expires_at"),
        "rate_limit_buckets",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_rate_limit_buckets_expires_at"), table_name="rate_limit_buckets")
    op.drop_table("rate_limit_buckets")
