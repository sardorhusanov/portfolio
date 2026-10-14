import asyncio


from alembic import context
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.connection import create_database_engine, database_url


def run_sync(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_online():
    engine = create_database_engine(get_settings().database_url, migrations=True)
    async with engine.connect() as connection:
        await connection.run_sync(run_sync)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(
        url=database_url(get_settings().database_url),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_online())
