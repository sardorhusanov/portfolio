from math import ceil

from app.core.content import sanitize_html
from app.core.exceptions import NotFoundError
from app.repositories.public import PublicRepository
from app.schemas.public import (
    Page,
    PostDetail,
    PostLink,
    PostSummary,
    ProfileOut,
    ProjectOut,
    TagOut,
)


class PublicService:
    def __init__(self, repository: PublicRepository) -> None:
        self.repository = repository

    async def profile(self) -> ProfileOut:
        value = await self.repository.profile()
        if value is None:
            raise NotFoundError("Profile has not been configured yet.")
        return ProfileOut.model_validate(value)

    async def posts(
        self, page: int, page_size: int, tag: str | None, featured: bool | None, year: int | None
    ) -> Page[PostSummary]:
        items, total = await self.repository.posts(page, page_size, tag, featured, year)
        return Page(
            items=[PostSummary.model_validate(p) for p in items],
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size),
        )

    async def post(self, slug: str) -> PostDetail:
        post = await self.repository.post(slug)
        if post is None:
            raise NotFoundError("Article not found.")
        previous, following = await self.repository.neighbors(post)
        result = PostDetail.model_validate(post)
        result.content_html = sanitize_html(post.content_html)
        result.previous = PostLink.model_validate(previous) if previous else None
        result.next = PostLink.model_validate(following) if following else None
        return result

    async def projects(
        self, page: int, page_size: int, featured: bool | None, status: str | None
    ) -> Page[ProjectOut]:
        items, total = await self.repository.projects(page, page_size, featured, status)
        return Page(
            items=[ProjectOut.model_validate(p) for p in items],
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size),
        )

    async def project(self, slug: str) -> ProjectOut:
        value = await self.repository.project(slug)
        if value is None:
            raise NotFoundError("Project not found.")
        return ProjectOut.model_validate(value)

    async def tags(self) -> list[TagOut]:
        return [TagOut.model_validate(tag) for tag in await self.repository.tags()]
