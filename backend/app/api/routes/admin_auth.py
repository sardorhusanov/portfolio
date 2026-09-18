from fastapi import APIRouter, Depends, Request, Response

from app.api.admin_dependencies import Auth, CurrentAdmin, csrf_guard
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.auth import AdminOut, AuthOut, LoginRequest

router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Authentication"])
COOKIE = "portfolio_refresh"
COOKIE_PATH = "/api/v1/admin/auth"


def set_cookie(response: Response, value: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE,
        value,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path=COOKIE_PATH,
        max_age=settings.refresh_token_expire_days * 86400,
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/login", response_model=AuthOut, dependencies=[Depends(csrf_guard)])
async def login(body: LoginRequest, request: Request, response: Response, service: Auth) -> AuthOut:
    limiter.check("login-global", 30)
    limiter.check("login:" + (request.client.host if request.client else "unknown"), 8)
    admin, access, refresh = await service.login(str(body.email), body.password)
    set_cookie(response, refresh)
    return AuthOut(admin=AdminOut.model_validate(admin), access_token=access)


@router.post("/refresh", response_model=AuthOut, dependencies=[Depends(csrf_guard)])
async def refresh(request: Request, response: Response, service: Auth) -> AuthOut:
    admin, access, value = await service.rotate(request.cookies.get(COOKIE))
    set_cookie(response, value)
    return AuthOut(admin=AdminOut.model_validate(admin), access_token=access)


@router.post("/logout", status_code=204, dependencies=[Depends(csrf_guard)])
async def logout(request: Request, service: Auth) -> Response:
    await service.logout(request.cookies.get(COOKIE))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        COOKIE,
        path=COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=get_settings().app_env == "production",
    )
    return response


@router.get("/me", response_model=AdminOut)
async def me(admin: CurrentAdmin) -> AdminOut:
    return AdminOut.model_validate(admin)
