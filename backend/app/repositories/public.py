from datetime import datetime, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Post, PostSlugHistory, Profile, Project, Tag


def public_posts() -> Select[tuple[Post]]:
    return select(Post).where(
        Post.status == "published", Post.published_at <= func.statement_timestamp()
    )


class PublicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def profile(self) -> Profile | None:
        return await self.session.get(Profile, 1)

    async def posts(
        self, page: int, page_size: int, tag: str | None, featured: bool | None, year: int | None
    ) -> tuple[list[Post], int]:
        query = public_posts()
        if tag:
            query = query.where(Post.tags.any(Tag.slug == tag))
        if featured is not None:
            query = query.where(Post.featured == featured)
        if year is not None:
            query = query.where(
                Post.published_at >= datetime(year, 1, 1, tzinfo=timezone.utc),
                Post.published_at < datetime(year + 1, 1, 1, tzinfo=timezone.utc),
            )
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.session.scalars(
            query.options(selectinload(Post.tags))
            .order_by(Post.published_at.desc(), Post.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), total or 0

    async def post(self, slug: str) -> Post | None:
        return await self.session.scalar(
            public_posts().where(
                or_(
                    Post.slug == slug,
                    Post.id.in_(
                        select(PostSlugHistory.post_id).where(PostSlugHistory.old_slug == slug)
                    ),
                )
            )
        )

    async def neighbors(self, post: Post) -> tuple[Post | None, Post | None]:
        from sqlalchemy import tuple_

        key = tuple_(Post.published_at, Post.id)
        current = tuple_(post.published_at, post.id)
        previous = await self.session.scalar(
            public_posts()
            .where(key < current)
            .order_by(Post.published_at.desc(), Post.id.desc())
            .limit(1)
        )
        following = await self.session.scalar(
            public_posts().where(key > current).order_by(Post.published_at, Post.id).limit(1)
        )
        return previous, following

    async def projects(
        self, page: int, page_size: int, featured: bool | None, status: str | None
    ) -> tuple[list[Project], int]:
        query = select(Project)
        if featured is not None:
            query = query.where(Project.featured == featured)
        if status:
            query = query.where(Project.status == status)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.session.scalars(
            query.order_by(Project.display_order, Project.created_at, Project.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result), total or 0

    async def project(self, slug: str) -> Project | None:
        return await self.session.scalar(select(Project).where(Project.slug == slug))

    async def tags(self) -> list[Tag]:
        result = await self.session.scalars(
            select(Tag)
            .where(
                Tag.posts.any(
                    (Post.status == "published") & (Post.published_at <= func.statement_timestamp())
                )
            )
            .order_by(Tag.name)
        )
        return list(result)

    async def feed_posts(self) -> list[Post]:
        return list(
            await self.session.scalars(
                public_posts().order_by(Post.published_at.desc(), Post.id.desc()).limit(30)
            )
        )

    async def sitemap_posts(self) -> list[tuple[str, datetime]]:
        rows = await self.session.execute(
            select(Post.slug, Post.updated_at).where(
                Post.status == "published", Post.published_at <= func.statement_timestamp()
            )
        )
        return [(row.slug, row.updated_at) for row in rows]
