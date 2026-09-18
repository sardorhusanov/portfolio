from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.admin_dependencies import get_admin
from app.api.dependencies import Session
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.integrations.telegram.service import TelegramSyncService
from app.repositories.admin import AdminRepository
from app.schemas.admin import (
    Confirmation,
    PostAdmin,
    ProfileInput,
    ProjectInput,
    ProjectUpdate,
    ReorderInput,
)
from app.schemas.public import ProfileOut, ProjectOut
from app.services.manage import ManagementService

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(get_admin)])


def management(session: Session) -> ManagementService:
    return ManagementService(AdminRepository(session))


Service = Annotated[ManagementService, Depends(management)]


@router.get("/overview", tags=["Admin Overview"])
async def overview(service: Service) -> dict:
    data = await service.repo.overview()
    return {
        "counts": data["counts"],
        "projects": data["projects"],
        "last_published": PostAdmin.model_validate(data["last_published"])
        if data["last_published"]
        else None,
        "drafts": [PostAdmin.model_validate(p) for p in data["drafts"]],
        "telegram_configured": bool(
            get_settings().telegram_bot_token and get_settings().telegram_channel_id
        ),
    }


@router.get("/projects", response_model=list[ProjectOut], tags=["Admin Projects"])
async def projects(service: Service):
    return [ProjectOut.model_validate(p) for p in await service.repo.all_projects()]


@router.post("/projects", response_model=ProjectOut, status_code=201, tags=["Admin Projects"])
async def create_project(body: ProjectInput, service: Service):
    return ProjectOut.model_validate(await service.create_project(body))


@router.put("/projects/reorder", response_model=list[ProjectOut], tags=["Admin Projects"])
async def reorder(body: ReorderInput, service: Service):
    return [ProjectOut.model_validate(p) for p in await service.reorder(body.ids)]


@router.get("/projects/{project_id}", response_model=ProjectOut, tags=["Admin Projects"])
async def project(project_id: UUID, service: Service):
    return ProjectOut.model_validate(await service.project(project_id))


@router.patch("/projects/{project_id}", response_model=ProjectOut, tags=["Admin Projects"])
async def update_project(project_id: UUID, body: ProjectUpdate, service: Service):
    return ProjectOut.model_validate(
        await service.update_project(project_id, body.data, body.expected_updated_at)
    )


@router.delete("/projects/{project_id}", status_code=204, tags=["Admin Projects"])
async def delete_project(project_id: UUID, body: Confirmation, service: Service):
    await service.delete_project(project_id)
    return Response(status_code=204)


@router.get("/profile", response_model=ProfileOut, tags=["Admin Profile"])
async def profile(service: Service):
    return ProfileOut.model_validate(await service.profile())


@router.put("/profile", response_model=ProfileOut, tags=["Admin Profile"])
async def save_profile(body: ProfileInput, service: Service):
    return ProfileOut.model_validate(await service.save_profile(body))


@router.post("/integrations/telegram/test", tags=["Integrations"])
async def test_telegram(service: Service):
    limiter.check("telegram-test", 10)
    return await TelegramSyncService(service.repo).test_connection()
