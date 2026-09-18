"""Explicit single-admin initialization. Never called by public seeding."""

import asyncio
import getpass
import os

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select

from app.core.security import password_hasher
from app.db.models import Admin
from app.db.session import SessionFactory, engine


async def main() -> None:
    email = str(
        TypeAdapter(EmailStr).validate_python(
            os.environ.get("ADMIN_EMAIL") or input("Email: ").strip()
        )
    ).lower()
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass(
        "Password (at least 12 characters): "
    )
    if len(password) < 12:
        raise SystemExit("Use a password of at least 12 characters.")
    if not os.environ.get("ADMIN_PASSWORD") and password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    async with SessionFactory() as session:
        if await session.scalar(select(Admin.id).limit(1)):
            raise SystemExit("An administrator already exists. No changes were made.")
        session.add(Admin(email=email, hashed_password=password_hasher.hash(password)))
        await session.commit()
    await engine.dispose()
    print("Administrator created.")


if __name__ == "__main__":
    asyncio.run(main())
