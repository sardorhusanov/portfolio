from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.admin_dependencies import get_admin
from app.api.dependencies import Session
from app.core.rate_limit import limiter
from app.integrations.telegram.service import TelegramSyncService
from app.repositories.admin import AdminRepository
from app.schemas.admin import Confirmation, PostAdmin, PostCreate, PostUpdate, RevisionInput
from app.schemas.public import Page
from app.services.posts import PostService

router = APIRouter(
    prefix="/api/v1/admin/posts", tags=["Admin Posts"], dependencies=[Depends(get_admin)]
)


def post_service(session: Session) -> PostService:
    return PostService(AdminRepository(session))


Service = Annotated[PostService, Depends(post_service)]


@router.get("", response_model=Page[PostAdmin])
async def posts(
    service: Service,
    status: Literal["draft", "published", "archived"] | None = None,
    search: str = Query(default="", max_length=240),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await service.list(status, search, page, page_size)


@router.post("", response_model=PostAdmin, status_code=201)
async def create(body: PostCreate, service: Service):
    return PostAdmin.model_validate(await service.create(body))


@router.get("/{post_id}", response_model=PostAdmin)
async def detail(post_id: UUID, service: Service):
    return PostAdmin.model_validate(await service.get(post_id))


@router.patch("/{post_id}", response_model=PostAdmin)
async def update(post_id: UUID, body: PostUpdate, service: Service):
    return PostAdmin.model_validate(await service.update(post_id, body))


@router.post("/{post_id}/publish", response_model=PostAdmin)
async def publish(post_id: UUID, body: RevisionInput, service: Service):
    return PostAdmin.model_validate(await service.status(post_id, "published", body.revision))


@router.post("/{post_id}/unpublish", response_model=PostAdmin)
async def unpublish(post_id: UUID, body: RevisionInput, service: Service):
    return PostAdmin.model_validate(await service.status(post_id, "draft", body.revision))


@router.post("/{post_id}/archive", response_model=PostAdmin)
async def archive(post_id: UUID, body: RevisionInput, service: Service):
    return PostAdmin.model_validate(await service.status(post_id, "archived", body.revision))


@router.delete("/{post_id}", status_code=204)
async def delete(post_id: UUID, body: Confirmation, service: Service):
    await service.delete(post_id)
    return Response(status_code=204)


@router.post("/{post_id}/telegram/sync", response_model=PostAdmin)
async def sync(post_id: UUID, service: Service):
    limiter.check("telegram-retry", 15)
    return PostAdmin.model_validate(await TelegramSyncService(service.repo).sync(post_id))


@router.post("/{post_id}/telegram/recreate", response_model=PostAdmin)
async def recreate(post_id: UUID, body: Confirmation, service: Service):
    limiter.check("telegram-recreate", 5)
    return PostAdmin.model_validate(
        await TelegramSyncService(service.repo).sync(post_id, recreate=True)
    )


@router.delete("/{post_id}/telegram/message", response_model=PostAdmin)
async def delete_message(post_id: UUID, body: Confirmation, service: Service):
    return PostAdmin.model_validate(await TelegramSyncService(service.repo).delete_message(post_id))


@router.get("/{post_id}/telegram/preview")
async def telegram_preview(post_id: UUID, service: Service) -> dict[str, str]:
    from app.integrations.telegram.formatter import announcement

    return {"html": announcement(await service.get(post_id), preview=True)}
