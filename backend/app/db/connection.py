"""Connection options shared by the API and database migrations."""

import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool


def database_url(value: str) -> URL:
    """Accept hosted Postgres URLs while keeping credentials out of diagnostics."""
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("DATABASE_URL must use PostgreSQL with asyncpg.")
    query = dict(url.query)
    if "channel_binding" in query:
        raise ValueError(
            "asyncpg does not accept channel_binding in DATABASE_URL. "
            "Use the provider's asyncpg connection URL with ssl=require or ssl=verify-full."
        )
    if "sslmode" in query:
        query.setdefault("ssl", query.pop("sslmode"))
    return url.set(query=query)


def create_database_engine(value: str, *, migrations: bool = False) -> AsyncEngine:
    options: dict = {"pool_pre_ping": True}
    if migrations or os.environ.get("VERCEL") == "1":
        # Serverless instances should not retain their own idle connection pools.
        options["poolclass"] = NullPool
    return create_async_engine(database_url(value), **options)
