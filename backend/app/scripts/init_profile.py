"""Initialize only a real owner's identity; never add sample projects or articles."""

import argparse
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.db.session import SessionFactory, engine


async def initialize_profile(session: AsyncSession, name: str, headline: str) -> bool:
    if await session.get(Profile, 1):
        return False
    session.add(
        Profile(
            name=name,
            headline=headline,
            short_bio="",
            long_bio="",
            location="",
            currently_building="",
            currently_learning="",
            skills={},
            timeline=[],
        )
    )
    await session.commit()
    return True


async def main(name: str, headline: str) -> None:
    try:
        async with SessionFactory() as session:
            created = await initialize_profile(session, name, headline)
        print("Profile initialized. Add your content in admin." if created else
              "Profile already exists; no changes were made.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--headline", required=True)
    args = parser.parse_args()
    if not 1 <= len(args.name.strip()) <= 150 or not 1 <= len(args.headline.strip()) <= 200:
        parser.error("Provide a name (1–150 characters) and headline (1–200 characters).")
    asyncio.run(main(args.name.strip(), args.headline.strip()))
