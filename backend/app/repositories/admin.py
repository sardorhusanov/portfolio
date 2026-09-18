from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.content import slugify
from app.db.models import Post, PostSlugHistory, Profile, Project, Tag


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def post(self, post_id: UUID, lock: bool = False) -> Post | None:
        query = select(Post).where(Post.id == post_id).execution_options(populate_existing=True)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def posts(
        self, status: str | None, search: str, page: int, size: int
    ) -> tuple[list[Post], int]:
        query = select(Post)
        if status:
            query = query.where(Post.status == status)
        if search:
            query = query.where(Post.title.icontains(search, autoescape=True))
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        posts = await self.session.scalars(
            query.order_by(Post.updated_at.desc(), Post.id).offset((page - 1) * size).limit(size)
        )
        return list(posts), total or 0

    async def slug_available(self, slug: str, post_id: UUID | None = None) -> bool:
        # Serialize the cross-table slug reservation check; unique indexes remain a final guard.
        await self.session.execute(select(func.pg_advisory_xact_lock(73819421)))
        post = await self.session.scalar(select(Post.id).where(Post.slug == slug))
        history = await self.session.scalar(
            select(PostSlugHistory.post_id).where(PostSlugHistory.old_slug == slug)
        )
        return (post is None or post == post_id) and (history is None or history == post_id)

    async def tags(self, names: list[str]) -> list[Tag]:
        result = []
        seen = set()
        for name in names:
            slug = slugify(name)
            if slug in seen:
                continue
            seen.add(slug)
            await self.session.execute(
                insert(Tag)
                .values(name=name.strip(), slug=slug)
                .on_conflict_do_nothing(index_elements=[Tag.slug])
            )
            result.append(await self.session.scalar(select(Tag).where(Tag.slug == slug)))
        return result

    async def record_slug(self, post_id: UUID, old_slug: str, new_slug: str) -> None:
        existing = await self.session.scalar(
            select(PostSlugHistory).where(
                PostSlugHistory.old_slug == new_slug, PostSlugHistory.post_id == post_id
            )
        )
        if existing:
            await self.session.delete(existing)
        old = await self.session.scalar(
            select(PostSlugHistory).where(PostSlugHistory.old_slug == old_slug)
        )
        if not old:
            self.session.add(PostSlugHistory(post_id=post_id, old_slug=old_slug))

    async def project(self, project_id: UUID, lock: bool = False) -> Project | None:
        query = select(Project).where(Project.id == project_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def all_projects(self) -> list[Project]:
        return list(
            await self.session.scalars(
                select(Project).order_by(Project.display_order, Project.created_at)
            )
        )

    async def profile(self) -> Profile | None:
        return await self.session.get(Profile, 1)

    async def overview(self) -> dict:
        counts = dict(
            (
                await self.session.execute(select(Post.status, func.count()).group_by(Post.status))
            ).all()
        )
        total = await self.session.scalar(select(func.count()).select_from(Project))
        last = await self.session.scalar(
            select(Post)
            .where(Post.status == "published")
            .order_by(Post.published_at.desc())
            .limit(1)
        )
        drafts, _ = await self.posts("draft", "", 1, 5)
        return {"counts": counts, "projects": total or 0, "last_published": last, "drafts": drafts}
