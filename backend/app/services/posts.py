import logging
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.content import reading_time, slugify
from app.core.errors import AppError
from app.core.exceptions import NotFoundError
from app.db.models import Post
from app.integrations.telegram.service import TelegramSyncService
from app.repositories.admin import AdminRepository
from app.schemas.admin import PostAdmin, PostCreate, PostFields, PostUpdate
from app.schemas.public import Page
from app.services.editor import excerpt_from, plain_text, render_document

log = logging.getLogger(__name__)


class PostService:
    def __init__(self, repository: AdminRepository) -> None:
        self.repo = repository

    async def get(self, post_id: UUID, lock: bool = False) -> Post:
        post = await self.repo.post(post_id, lock)
        if not post:
            raise NotFoundError("Article not found.")
        return post

    async def list(self, status: str | None, search: str, page: int, size: int) -> Page[PostAdmin]:
        posts, total = await self.repo.posts(status, search, page, size)
        return Page(
            items=[PostAdmin.model_validate(p) for p in posts],
            total=total,
            page=page,
            page_size=size,
            pages=ceil(total / size),
        )

    async def commit(self) -> None:
        try:
            await self.repo.session.commit()
        except IntegrityError:
            await self.repo.session.rollback()
            raise AppError("That slug is already in use. Choose another slug.", 409) from None

    async def create(self, data: PostCreate) -> Post:
        slug = data.slug or slugify(data.title)
        if not await self.repo.slug_available(slug):
            raise AppError("That slug is already in use. Choose another slug.", 409)
        values = data.model_dump(exclude={"tags", "content_json", "slug"})
        html = render_document(data.content_json)
        values["excerpt"] = values["excerpt"] or excerpt_from(html)
        post = Post(
            **values,
            slug=slug,
            content_json=data.content_json,
            content_html=html,
            reading_time_minutes=reading_time(html),
            tags=await self.repo.tags(data.tags),
            telegram_sync_status="not_synced",
        )
        self.repo.session.add(post)
        await self.commit()
        return post

    @staticmethod
    def check_revision(post: Post, revision: int) -> None:
        if post.revision != revision:
            raise AppError(
                "This article changed in another tab. Reload before saving; your local "
                "text has not been overwritten.",
                409,
            )

    async def update(self, post_id: UUID, data: PostUpdate) -> Post:
        post = await self.get(post_id, lock=True)
        self.check_revision(post, data.revision)
        changes = data.model_dump(exclude_unset=True, exclude={"revision", "autosave"})
        for key in ["title", "slug", "content_json", "featured", "tags"]:
            if key in changes and changes[key] is None:
                raise AppError(f"{key} cannot be null.", 422)
        # Reuse creation validation for tag names and all merged editable fields.
        merged = {
            key: getattr(post, key)
            for key in PostFields.model_fields
            if key not in {"tags", "content_json"}
        }
        merged.update(
            {
                "tags": [tag.name for tag in post.tags],
                "content_json": post.content_json or {"type": "doc", "content": []},
            }
        )
        merged.update(changes)
        try:
            validated = PostFields.model_validate(merged)
        except ValidationError:
            raise AppError(
                "Check the article settings, tag names, and field lengths.", 422
            ) from None
        if "slug" in changes and changes["slug"] != post.slug:
            if not await self.repo.slug_available(changes["slug"], post.id):
                raise AppError("That slug is already in use, including an old article URL.", 409)
            if post.published_at:
                await self.repo.record_slug(post.id, post.slug, changes["slug"])
        for key, value in changes.items():
            if key == "tags":
                post.tags = await self.repo.tags(validated.tags)
            else:
                setattr(post, key, value)
        if "content_json" in changes:
            post.content_html = render_document(validated.content_json)
            post.reading_time_minutes = reading_time(post.content_html)
        if not post.excerpt:
            post.excerpt = excerpt_from(post.content_html)
        post.revision += 1
        if data.autosave:
            post.last_autosaved_at = datetime.now(timezone.utc)
        if post.status == "published" and post.telegram_sync_status != "pending":
            post.telegram_sync_status = "not_synced"
        await self.commit()
        if post.status == "published":
            return await TelegramSyncService(self.repo).after_save(post_id)
        return post

    async def status(self, post_id: UUID, status: str, revision: int) -> Post:
        post = await self.get(post_id, lock=True)
        if not (status == "published" and post.status == "published"):
            self.check_revision(post, revision)
        if status == "published":
            if not post.title.strip() or not post.slug or not plain_text(post.content_html).strip():
                raise AppError("Add a title and meaningful article text before publishing.", 422)
            post.published_at = post.published_at or datetime.now(timezone.utc)
        if post.status != status:
            post.status = status
            post.revision += 1
        await self.commit()
        log.info("post_status_changed", extra={"post_id": str(post.id), "post_status": status})
        if status == "published":
            return await TelegramSyncService(self.repo).after_save(post_id)
        return post

    async def delete(self, post_id: UUID) -> None:
        post = await self.get(post_id, lock=True)
        if post.telegram_sync_status == "pending":
            raise AppError("Wait for Telegram synchronization before deleting this article.", 409)
        await self.repo.session.delete(post)
        await self.repo.session.commit()
