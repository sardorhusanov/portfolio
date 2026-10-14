from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.db.connection import create_database_engine

engine = create_database_engine(get_settings().database_url)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
