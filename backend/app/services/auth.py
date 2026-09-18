import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import DUMMY_HASH, access_token, decode_access, token_digest, verify_password
from app.db.models import Admin, AdminSession, RefreshToken
from app.repositories.auth import AuthRepository

log = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repo = repository

    async def login(self, email: str, password: str) -> tuple[Admin, str, str]:
        admin = await self.repo.by_email(email)
        valid = await run_in_threadpool(
            verify_password, password, admin.hashed_password if admin else DUMMY_HASH
        )
        if not admin or not valid:
            log.info("admin_login_failed")
            raise AppError("Invalid email or password.", 401)
        now = datetime.now(timezone.utc)
        admin.last_login_at = now
        session = AdminSession(
            admin_id=admin.id,
            expires_at=now + timedelta(days=get_settings().refresh_token_expire_days),
        )
        self.repo.session.add(session)
        await self.repo.session.flush()
        refresh = await self._new_refresh(session)
        await self.repo.session.commit()
        log.info("admin_login_success")
        return admin, access_token(admin.id, session.id), refresh

    async def _new_refresh(self, session: AdminSession) -> str:
        value = secrets.token_urlsafe(48)
        self.repo.session.add(
            RefreshToken(
                session_id=session.id, digest=token_digest(value), expires_at=session.expires_at
            )
        )
        return value

    async def rotate(self, value: str | None) -> tuple[Admin, str, str]:
        if not value:
            raise AppError("Please sign in again.", 401)
        token = await self.repo.refresh(token_digest(value))
        now = datetime.now(timezone.utc)
        if not token:
            raise AppError("Please sign in again.", 401)
        session = await self.repo.session.get(AdminSession, token.session_id, with_for_update=True)
        if token.used_at or token.expires_at <= now or session.revoked_at:
            session.revoked_at = now
            await self.repo.session.commit()
            raise AppError("Please sign in again.", 401)
        token.used_at = now
        replacement = await self._new_refresh(session)
        admin = await self.repo.admin(session.admin_id)
        await self.repo.session.commit()
        return admin, access_token(admin.id, session.id), replacement

    async def authenticate(self, value: str) -> Admin:
        try:
            claims = decode_access(value)
            if claims["type"] != "access":
                raise ValueError()
            admin_id, session_id = UUID(claims["sub"]), UUID(claims["sid"])
        except (jwt.PyJWTError, ValueError, KeyError):
            raise AppError("Please sign in again.", 401) from None
        if not await self.repo.active_session(session_id, admin_id):
            raise AppError("Please sign in again.", 401)
        admin = await self.repo.admin(admin_id)
        if not admin:
            raise AppError("Please sign in again.", 401)
        return admin

    async def logout(self, value: str | None) -> None:
        if value:
            token = await self.repo.refresh(token_digest(value))
            if token:
                session = await self.repo.session.get(AdminSession, token.session_id)
                session.revoked_at = datetime.now(timezone.utc)
                await self.repo.session.commit()
