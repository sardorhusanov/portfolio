import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

password_hasher = PasswordHasher()
DUMMY_HASH = password_hasher.hash("not-a-real-admin-password")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def access_token(admin_id: UUID, session_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(admin_id),
            "sid": str(session_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
            "iss": "portfolio-admin",
            "aud": "portfolio-admin",
        },
        settings.secret_key,
        algorithm="HS256",
    )


def decode_access(value: str) -> dict:
    return jwt.decode(
        value,
        get_settings().secret_key,
        algorithms=["HS256"],
        audience="portfolio-admin",
        issuer="portfolio-admin",
        options={"require": ["exp", "iat", "sub", "sid", "type"]},
    )
