"""Add admin sessions editor metadata uploads and slug history"""

import sqlalchemy as sa

from alembic import op

revision = "1493b09f19f6"
down_revision = "bf7c7048f114"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("singleton", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("singleton = 1", name=op.f("ck_admins_singleton")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admins")),
        sa.UniqueConstraint("email", name=op.f("uq_admins_email")),
        sa.UniqueConstraint("singleton", name=op.f("uq_admins_singleton")),
    )
    op.create_table(
        "uploads",
        sa.Column("storage_key", sa.String(length=200), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=50), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_uploads")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_uploads_storage_key")),
    )
    op.create_table(
        "admin_sessions",
        sa.Column("admin_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["admins.id"],
            name=op.f("fk_admin_sessions_admin_id_admins"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_sessions")),
    )
    op.create_index(
        op.f("ix_admin_sessions_admin_id"), "admin_sessions", ["admin_id"], unique=False
    )
    op.create_table(
        "post_slug_history",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("old_slug", sa.String(length=260), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            name=op.f("fk_post_slug_history_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_post_slug_history")),
        sa.UniqueConstraint("old_slug", name=op.f("uq_post_slug_history_old_slug")),
    )
    op.create_index(
        op.f("ix_post_slug_history_post_id"), "post_slug_history", ["post_id"], unique=False
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["admin_sessions.id"],
            name=op.f("fk_refresh_tokens_session_id_admin_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("digest", name=op.f("uq_refresh_tokens_digest")),
    )
    op.create_index(
        op.f("ix_refresh_tokens_session_id"), "refresh_tokens", ["session_id"], unique=False
    )
    op.add_column("posts", sa.Column("telegram_message_type", sa.String(length=10), nullable=True))
    op.add_column("posts", sa.Column("telegram_error", sa.Text(), nullable=True))
    op.add_column(
        "posts",
        sa.Column(
            "telegram_delivery_uncertain", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "posts", sa.Column("telegram_sync_started_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "posts", sa.Column("last_autosaved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("posts", sa.Column("revision", sa.Integer(), server_default="1", nullable=False))
    op.add_column("posts", sa.Column("cover_image_alt", sa.String(length=300), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "cover_image_alt")
    op.drop_column("posts", "revision")
    op.drop_column("posts", "last_autosaved_at")
    op.drop_column("posts", "telegram_sync_started_at")
    op.drop_column("posts", "telegram_delivery_uncertain")
    op.drop_column("posts", "telegram_error")
    op.drop_column("posts", "telegram_message_type")
    op.drop_index(op.f("ix_refresh_tokens_session_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_post_slug_history_post_id"), table_name="post_slug_history")
    op.drop_table("post_slug_history")
    op.drop_index(op.f("ix_admin_sessions_admin_id"), table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_table("uploads")
    op.drop_table("admins")
