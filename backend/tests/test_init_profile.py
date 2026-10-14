import pytest
from sqlalchemy import func, select

from app.db.models import Post, Profile, Project
from app.scripts.init_profile import initialize_profile


@pytest.mark.asyncio
async def test_initialization_has_no_sample_content_and_never_overwrites(session):
    assert await initialize_profile(session, "Real Owner", "Computer Science student")
    assert not await initialize_profile(session, "Different Owner", "Different headline")
    profile = await session.get(Profile, 1)
    assert profile.name == "Real Owner"
    assert profile.skills == {} and profile.timeline == []
    assert profile.github_url is None and profile.email is None
    assert await session.scalar(select(func.count()).select_from(Post)) == 0
    assert await session.scalar(select(func.count()).select_from(Project)) == 0
