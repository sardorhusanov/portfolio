from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagOut(ORMModel):
    id: UUID
    name: str
    slug: str


class PostSummary(ORMModel):
    id: UUID
    title: str
    slug: str
    excerpt: str | None
    cover_image_url: str | None
    featured: bool
    published_at: datetime
    reading_time_minutes: int
    tags: list[TagOut]


class PostLink(ORMModel):
    title: str
    slug: str


class PostDetail(PostSummary):
    cover_image_alt: str | None = None
    content_html: str
    seo_title: str | None
    seo_description: str | None
    previous: PostLink | None = None
    next: PostLink | None = None


class ProjectOut(ORMModel):
    id: UUID
    name: str
    slug: str
    short_description: str
    description: str
    cover_image_url: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str]
    status: str
    featured: bool
    display_order: int
    started_at: date | None
    created_at: datetime
    updated_at: datetime


class ProfileOut(ORMModel):
    name: str
    headline: str
    short_bio: str
    long_bio: str
    location: str
    avatar_url: str | None
    github_url: str | None
    telegram_url: str | None
    linkedin_url: str | None
    email: str | None
    currently_building: str
    currently_learning: str
    skills: dict[str, list[str]]
    story: str
    interests: str
    philosophy: str
    timeline: list[dict[str, str]]
