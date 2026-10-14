import asyncio
import os
from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.core.rate_limit as rate_limit
from app.core.errors import AppError
from app.core.rate_limit import DatabaseRateLimiter, RateLimiter
from app.db.models import RateLimitBucket


@pytest_asyncio.fixture
async def rate_database():
    url = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_test"
    )
    if not (make_url(url).database or "").endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL must use a dedicated database ending in _test")
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    prefix = "rate-test-" + uuid4().hex + ":"
    try:
        yield factory, prefix
    finally:
        async with factory.begin() as session:
            await session.execute(
                delete(RateLimitBucket).where(RateLimitBucket.key.startswith(prefix))
            )
        await engine.dispose()


def test_local_sliding_window_preserves_exact_boundary(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(rate_limit, "monotonic", lambda: now[0])
    limiter = RateLimiter()
    limiter.check("login", 2)
    now[0] = 110.0
    limiter.check("login", 2)
    now[0] = 159.0
    with pytest.raises(AppError) as rejected:
        limiter.check("login", 2)
    assert rejected.value.status == 429
    now[0] = 160.0
    limiter.check("login", 2)
    with pytest.raises(AppError):
        limiter.check("login", 2)


async def test_vercel_uses_shared_limiter_and_local_keeps_memory_limiter(monkeypatch):
    shared = AsyncMock()
    monkeypatch.setattr(rate_limit, "shared_limiter", shared)
    monkeypatch.setattr(rate_limit, "limiter", RateLimiter())
    monkeypatch.setenv("VERCEL", "1")
    await rate_limit.check_rate_limit("login", 8, 30)
    shared.check.assert_awaited_once_with("login", 8, 30)
    monkeypatch.delenv("VERCEL")
    await rate_limit.check_rate_limit("local", 1)
    with pytest.raises(AppError) as rejected:
        await rate_limit.check_rate_limit("local", 1)
    assert rejected.value.status == 429
    assert shared.check.await_count == 1


async def test_concurrent_instances_share_one_atomic_limit(rate_database):
    factory, prefix = rate_database
    instances = [DatabaseRateLimiter(factory), DatabaseRateLimiter(factory)]
    # Isolate the contention test from the separately tested expiration cleanup.
    for limiter in instances:
        limiter.next_cleanup = float("inf")
    outcomes = await asyncio.gather(
        *(instances[i % 2].check(prefix + "concurrent", 8) for i in range(32)),
        return_exceptions=True,
    )
    assert sum(result is None for result in outcomes) == 8
    rejected = [result for result in outcomes if result is not None]
    assert len(rejected) == 24
    assert all(isinstance(result, AppError) and result.status == 429 for result in rejected)
    # A fresh instance cannot reset the count.
    with pytest.raises(AppError) as error:
        await DatabaseRateLimiter(factory).check(prefix + "concurrent", 8)
    assert error.value.status == 429


async def test_shared_window_expires_individual_events_without_extending_on_rejection(
    rate_database,
):
    factory, prefix = rate_database
    key = prefix + "sliding"
    limiter = DatabaseRateLimiter(factory)
    await limiter.check(key, 2)
    await limiter.check(key, 2)
    async with factory() as session:
        original = await session.get(RateLimitBucket, key)
        original_events, original_expiry = original.events, original.expires_at
    with pytest.raises(AppError):
        await limiter.check(key, 2)
    async with factory.begin() as session:
        unchanged = await session.get(RateLimitBucket, key)
        assert unchanged.events == original_events
        assert unchanged.expires_at == original_expiry
        now = await session.scalar(select(func.clock_timestamp()))
        await session.execute(
            update(RateLimitBucket)
            .where(RateLimitBucket.key == key)
            .values(events=[now - timedelta(seconds=61), now])
        )
    await limiter.check(key, 2)
    with pytest.raises(AppError):
        await DatabaseRateLimiter(factory).check(key, 2)
    # Other action buckets remain independent.
    await limiter.check(prefix + "other", 2)


async def test_rate_limit_commit_survives_unrelated_transaction_rollback(rate_database):
    factory, prefix = rate_database
    limiter = DatabaseRateLimiter(factory)
    async with factory() as content_session:
        now = await content_session.scalar(select(func.clock_timestamp()))
        content_session.add(
            RateLimitBucket(
                key=prefix + "uncommitted", events=[], expires_at=now + timedelta(minutes=5)
            )
        )
        await content_session.flush()
        await limiter.check(prefix + "attempt", 1)
        await content_session.rollback()
    async with factory() as session:
        assert await session.get(RateLimitBucket, prefix + "uncommitted") is None
    with pytest.raises(AppError) as rejected:
        await DatabaseRateLimiter(factory).check(prefix + "attempt", 1)
    assert rejected.value.status == 429


async def test_cleanup_removes_expired_buckets_and_skips_locked_rows(rate_database):
    factory, prefix = rate_database
    async with factory.begin() as session:
        now = await session.scalar(select(func.clock_timestamp()))
        session.add_all(
            [
                RateLimitBucket(key=prefix + "expired", events=[], expires_at=now),
                RateLimitBucket(key=prefix + "locked", events=[], expires_at=now),
                RateLimitBucket(
                    key=prefix + "active", events=[now], expires_at=now + timedelta(minutes=1)
                ),
            ]
        )
    limiter = DatabaseRateLimiter(factory)
    async with factory.begin() as locked_session:
        await locked_session.execute(
            select(RateLimitBucket)
            .where(RateLimitBucket.key == prefix + "locked")
            .with_for_update()
        )
        await asyncio.wait_for(limiter.cleanup(), timeout=2)
        async with factory() as session:
            assert await session.get(RateLimitBucket, prefix + "expired") is None
            assert await session.get(RateLimitBucket, prefix + "locked") is not None
            assert await session.get(RateLimitBucket, prefix + "active") is not None
    limiter.next_cleanup = 0
    await limiter.cleanup()
    async with factory() as session:
        assert await session.get(RateLimitBucket, prefix + "locked") is None
