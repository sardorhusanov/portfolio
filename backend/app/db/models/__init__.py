from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Identity, Timestamps

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Identity, Base):
    __tablename__ = "tags"
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    posts: Mapped[list["Post"]] = relationship(secondary=post_tags, back_populates="tags")


class Post(Timestamps, Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="status"),
        CheckConstraint("reading_time_minutes >= 1", name="reading_time"),
        CheckConstraint(
            "status != 'published' OR published_at IS NOT NULL", name="publication_date"
        ),
        Index("ix_posts_publication", "status", "published_at"),
    )
    title: Mapped[str] = mapped_column(String(240))
    slug: Mapped[str] = mapped_column(String(260), unique=True)
    excerpt: Mapped[str | None] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    content_html: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reading_time_minutes: Mapped[int] = mapped_column(Integer, default=1)
    seo_title: Mapped[str | None] = mapped_column(String(240))
    seo_description: Mapped[str | None] = mapped_column(Text)
    telegram_message_id: Mapped[str | None] = mapped_column(String(100))
    telegram_channel_id: Mapped[str | None] = mapped_column(String(100))
    telegram_sync_status: Mapped[str | None] = mapped_column(String(40))
    telegram_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    telegram_message_type: Mapped[str | None] = mapped_column(String(10))
    telegram_error: Mapped[str | None] = mapped_column(Text)
    telegram_delivery_uncertain: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    telegram_sync_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_autosaved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    cover_image_alt: Mapped[str | None] = mapped_column(String(300))
    tags: Mapped[list[Tag]] = relationship(
        secondary=post_tags, back_populates="posts", lazy="selectin"
    )


class Project(Timestamps, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'archived', 'experimental')", name="status"
        ),
    )
    name: Mapped[str] = mapped_column(String(180))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    short_description: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    live_url: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list[str]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[date | None] = mapped_column(Date)


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(150))
    headline: Mapped[str] = mapped_column(String(200))
    short_bio: Mapped[str] = mapped_column(Text)
    long_bio: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(150))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    telegram_url: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(254))
    currently_building: Mapped[str] = mapped_column(Text)
    currently_learning: Mapped[str] = mapped_column(Text)
    skills: Mapped[dict[str, list[str]]] = mapped_column(JSONB, default=dict)
    story: Mapped[str] = mapped_column(Text, default="")
    interests: Mapped[str] = mapped_column(Text, default="")
    philosophy: Mapped[str] = mapped_column(Text, default="")
    timeline: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)


class Admin(Timestamps, Base):
    __tablename__ = "admins"
    __table_args__ = (CheckConstraint("singleton = 1", name="singleton"),)
    singleton: Mapped[int] = mapped_column(Integer, unique=True, default=1)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminSession(Identity, Base):
    __tablename__ = "admin_sessions"
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Identity, Base):
    __tablename__ = "refresh_tokens"
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("admin_sessions.id", ondelete="CASCADE"), index=True
    )
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PostSlugHistory(Identity, Base):
    __tablename__ = "post_slug_history"
    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    old_slug: Mapped[str] = mapped_column(String(260), unique=True)


class Upload(Identity, Base):
    __tablename__ = "uploads"
    storage_key: Mapped[str] = mapped_column(String(200), unique=True)
    url: Mapped[str] = mapped_column(Text)
    original_name: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(50))
    size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
