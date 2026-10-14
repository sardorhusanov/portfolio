import os
from collections import OrderedDict, deque
from datetime import timedelta
from time import monotonic

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import AppError
from app.db.models import RateLimitBucket
from app.db.session import SessionFactory


class RateLimiter:
    """Bounded per-process sliding window for local, single-worker deployments."""

    def __init__(self) -> None:
        self.buckets: OrderedDict[str, deque[float]] = OrderedDict()

    def check(self, key: str, limit: int, seconds: int = 60) -> None:
        now = monotonic()
        bucket = self.buckets.setdefault(key, deque())
        self.buckets.move_to_end(key)
        while bucket and bucket[0] <= now - seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise AppError("Too many attempts. Please wait a minute and try again.", 429)
        bucket.append(now)
        if len(self.buckets) > 5000:
            self.buckets.popitem(last=False)


limiter = RateLimiter()


class DatabaseRateLimiter:
    """Share rolling windows across serverless instances using short PostgreSQL locks."""

    def __init__(self, factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self.factory = factory or SessionFactory
        self.next_cleanup = 0.0

    async def cleanup(self) -> None:
        if monotonic() < self.next_cleanup:
            return
        # A separate transaction releases cleanup locks before any bucket is acquired.
        # Skip busy buckets so cleanup cannot delay an in-flight rate-limit check.
        expired = (
            select(RateLimitBucket.key)
            .where(RateLimitBucket.expires_at <= func.clock_timestamp())
            .order_by(RateLimitBucket.expires_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        async with self.factory.begin() as session:
            await session.execute(delete(RateLimitBucket).where(RateLimitBucket.key.in_(expired)))
        self.next_cleanup = monotonic() + 60

    async def check(self, key: str, limit: int, seconds: int = 60) -> None:
        await self.cleanup()
        # This transaction is independent of content/authentication transactions: even
        # failed logins must count, and checking a limit must never commit other work.
        async with self.factory.begin() as session:
            statement = insert(RateLimitBucket).values(
                key=key, events=[], expires_at=func.clock_timestamp()
            )
            statement = statement.on_conflict_do_update(
                index_elements=[RateLimitBucket.key], set_={"key": statement.excluded.key}
            ).returning(RateLimitBucket.events, func.clock_timestamp().label("checked_at"))
            # UPSERT holds this bucket's row lock until commit. RETURNING evaluates the
            # database clock after the lock is acquired, avoiding instance clock skew.
            row = (await session.execute(statement)).one()
            cutoff = row.checked_at - timedelta(seconds=seconds)
            events = [event for event in row.events if event > cutoff]
            allowed = len(events) < limit
            if allowed:
                await session.execute(
                    update(RateLimitBucket)
                    .where(RateLimitBucket.key == key)
                    .values(
                        events=[*events, row.checked_at],
                        expires_at=row.checked_at + timedelta(seconds=seconds),
                    )
                )
        if not allowed:
            raise AppError("Too many attempts. Please wait a minute and try again.", 429)


shared_limiter = DatabaseRateLimiter()


async def check_rate_limit(key: str, limit: int, seconds: int = 60) -> None:
    if os.environ.get("VERCEL") == "1":
        await shared_limiter.check(key, limit, seconds)
    else:
        limiter.check(key, limit, seconds)
