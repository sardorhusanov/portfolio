import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    admin_auth,
    admin_manage,
    admin_posts,
    admin_uploads,
    feeds,
    pages,
    public,
)
from app.core import content  # noqa: F401 — register ORM content hooks
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.exceptions import NotFoundError
from app.core.middleware import BodyLimitMiddleware
from app.db.session import engine
from app.integrations.telegram.client import close_client
from app.services.pages import DIST


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_client()
    await engine.dispose()


settings = get_settings()
app = FastAPI(title="Sardorbek's portfolio", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url.rstrip("/")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Protection"],
)
app.add_middleware(BodyLimitMiddleware)
app.include_router(admin_auth.router)
app.include_router(admin_posts.router)
app.include_router(admin_manage.router)
app.include_router(admin_uploads.router)
app.include_router(public.router)
app.include_router(feeds.router)


@app.exception_handler(AppError)
async def application_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logging.getLogger(__name__).exception("Database operation failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Content is temporarily unavailable."})


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Process liveness. Database availability is checked by Compose independently."""
    return {"status": "ok"}


# The public API and feeds take priority over the SPA fallback.
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.include_router(pages.router)
