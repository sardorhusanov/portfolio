import pytest
from sqlalchemy.pool import NullPool

from app.db.connection import create_database_engine, database_url


def test_hosted_postgres_url_keeps_encoded_credentials_and_tls():
    url = database_url("postgresql://owner:p%40ss%2Fword@db.example/portfolio?sslmode=verify-full")
    assert url.drivername == "postgresql+asyncpg"
    assert url.password == "p@ss/word"
    assert url.query == {"ssl": "verify-full"}
    assert "p@ss" not in str(url)


def test_neon_url_keeps_tls_without_unsupported_libpq_option():
    url = database_url(
        "postgresql://owner:secret@db.example/portfolio?sslmode=require&channel_binding=require"
    )
    assert url.query == {"ssl": "require"}


def test_unsupported_driver_and_channel_binding_fail_without_credentials():
    for value in [
        "mysql://owner:secret@db.example/portfolio",
        "postgres://owner:secret@db.example/portfolio?channel_binding=require",
    ]:
        with pytest.raises(ValueError) as error:
            database_url(value)
        assert "secret" not in str(error.value)


@pytest.mark.asyncio
async def test_serverless_and_migrations_do_not_keep_idle_pools(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    runtime = create_database_engine("postgresql://localhost/portfolio")
    assert isinstance(runtime.pool, NullPool)
    await runtime.dispose()
    monkeypatch.delenv("VERCEL")
    migration = create_database_engine("postgresql://localhost/portfolio", migrations=True)
    assert isinstance(migration.pool, NullPool)
    await migration.dispose()
