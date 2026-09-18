from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import Session
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import Admin
from app.repositories.auth import AuthRepository
from app.services.auth import AuthService

bearer = HTTPBearer(auto_error=False)


def auth_service(session: Session) -> AuthService:
    return AuthService(AuthRepository(session))


Auth = Annotated[AuthService, Depends(auth_service)]


async def get_admin(
    service: Auth, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> Admin:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppError("Please sign in again.", 401)
    return await service.authenticate(credentials.credentials)


CurrentAdmin = Annotated[Admin, Depends(get_admin)]


def csrf_guard(request: Request) -> None:
    settings = get_settings()
    origins = {settings.frontend_url.rstrip("/"), settings.site_url.rstrip("/")}
    if (
        request.headers.get("origin") not in origins
        or request.headers.get("x-csrf-protection") != "1"
    ):
        raise AppError("Request origin is not allowed.", 403)
