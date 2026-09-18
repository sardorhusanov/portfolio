from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.public import ORMModel, TagOut
from app.services.editor import safe_url


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PostFields(Input):
    title: str = Field(min_length=1, max_length=240)
    slug: str | None = Field(default=None, max_length=260, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    excerpt: str | None = Field(default=None, max_length=2000)
    content_json: dict[str, Any] = Field(
        default_factory=lambda: {"type": "doc", "content": [{"type": "paragraph"}]}
    )
    cover_image_url: str | None = Field(default=None, max_length=2048)
    cover_image_alt: str | None = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list, max_length=20)
    featured: bool = False
    seo_title: str | None = Field(default=None, max_length=240)
    seo_description: str | None = Field(default=None, max_length=1000)

    @field_validator("cover_image_url")
    @classmethod
    def image_url(cls, value):
        return safe_url(value, image=True) if value else None

    @field_validator("tags")
    @classmethod
    def tag_names(cls, values):
        if any(not v.strip() or len(v.strip()) > 80 for v in values):
            raise ValueError("Tag names must contain 1–80 characters")
        return list(dict.fromkeys(v.strip() for v in values))


class PostCreate(PostFields):
    pass


class PostUpdate(Input):
    revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=240)
    slug: str | None = Field(default=None, max_length=260, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    excerpt: str | None = Field(default=None, max_length=2000)
    content_json: dict[str, Any] | None = None
    cover_image_url: str | None = Field(default=None, max_length=2048)
    cover_image_alt: str | None = Field(default=None, max_length=300)
    tags: list[str] | None = Field(default=None, max_length=20)
    featured: bool | None = None
    seo_title: str | None = Field(default=None, max_length=240)
    seo_description: str | None = Field(default=None, max_length=1000)
    autosave: bool = False

    _image_url = field_validator("cover_image_url")(PostFields.image_url.__func__)


class RevisionInput(Input):
    revision: int = Field(ge=1)


class Confirmation(Input):
    confirm: Literal[True]


class PostAdmin(ORMModel):
    id: UUID
    title: str
    slug: str
    excerpt: str | None
    content_json: dict[str, Any] | None
    content_html: str
    cover_image_url: str | None
    cover_image_alt: str | None
    status: str
    featured: bool
    tags: list[TagOut]
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    reading_time_minutes: int
    revision: int
    seo_title: str | None
    seo_description: str | None
    last_autosaved_at: datetime | None
    telegram_message_id: str | None
    telegram_channel_id: str | None
    telegram_message_type: str | None
    telegram_sync_status: str | None
    telegram_error: str | None
    telegram_delivery_uncertain: bool
    telegram_synced_at: datetime | None


class ProjectInput(Input):
    name: str = Field(min_length=1, max_length=180)
    slug: str | None = Field(default=None, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    short_description: str = Field(min_length=1, max_length=2000)
    description: str = Field(default="", max_length=20000)
    cover_image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    technologies: list[str] = Field(default_factory=list, max_length=30)
    status: Literal["active", "completed", "archived", "experimental"] = "active"
    featured: bool = False
    display_order: int = Field(default=0, ge=0, le=100000)
    started_at: date | None = None

    @field_validator("cover_image_url", "github_url", "live_url")
    @classmethod
    def urls(cls, value):
        return safe_url(value, image=True) if value else None

    @field_validator("technologies")
    @classmethod
    def technologies_valid(cls, values):
        if any(not v.strip() or len(v) > 80 for v in values):
            raise ValueError("Technology names must contain 1–80 characters")
        return list(dict.fromkeys(v.strip() for v in values))


class ProjectUpdate(Input):
    expected_updated_at: datetime
    data: ProjectInput


class ReorderInput(Input):
    ids: list[UUID] = Field(min_length=1, max_length=500)


class ProfileInput(Input):
    name: str = Field(min_length=1, max_length=150)
    headline: str = Field(min_length=1, max_length=200)
    short_bio: str = Field(max_length=3000)
    long_bio: str = Field(max_length=30000)
    location: str = Field(max_length=150)
    avatar_url: str | None = None
    github_url: str | None = None
    telegram_url: str | None = None
    linkedin_url: str | None = None
    email: EmailStr | None = None
    currently_building: str = Field(max_length=2000)
    currently_learning: str = Field(max_length=2000)
    skills: dict[str, list[str]] = Field(default_factory=dict, max_length=20)
    story: str = Field(default="", max_length=30000)
    interests: str = Field(default="", max_length=10000)
    philosophy: str = Field(default="", max_length=10000)
    timeline: list[dict[str, str]] = Field(default_factory=list, max_length=50)

    @field_validator("avatar_url", "github_url", "telegram_url", "linkedin_url")
    @classmethod
    def urls(cls, value):
        return safe_url(value, image=True) if value else None

    @field_validator("skills")
    @classmethod
    def skill_groups(cls, value):
        if any(
            not name.strip()
            or len(name) > 80
            or len(items) > 40
            or any(not item.strip() or len(item) > 100 for item in items)
            for name, items in value.items()
        ):
            raise ValueError("Use short group and skill names")
        return value


class UploadOut(ORMModel):
    id: UUID
    url: str
    original_name: str
    media_type: str
    size: int
    width: int
    height: int
