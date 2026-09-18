from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Admin, AdminSession, RefreshToken


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def by_email(self, email: str) -> Admin | None:
        return await self.session.scalar(select(Admin).where(Admin.email == email.lower()))

    async def active_session(self, session_id: UUID, admin_id: UUID) -> AdminSession | None:
        return await self.session.scalar(
            select(AdminSession).where(
                AdminSession.id == session_id,
                AdminSession.admin_id == admin_id,
                AdminSession.revoked_at.is_(None),
                AdminSession.expires_at > datetime.now(timezone.utc),
            )
        )

    async def refresh(self, digest: str) -> RefreshToken | None:
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.digest == digest).with_for_update()
        )

    async def admin(self, admin_id: UUID) -> Admin | None:
        return await self.session.get(Admin, admin_id)
