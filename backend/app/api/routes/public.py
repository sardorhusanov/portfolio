from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Session
from app.repositories.public import PublicRepository
from app.schemas.public import Page, PostDetail, PostSummary, ProfileOut, ProjectOut, TagOut
from app.services.public import PublicService

router = APIRouter(prefix="/api/v1", tags=["public"])


def get_service(session: Session) -> PublicService:
    return PublicService(PublicRepository(session))


Service = Annotated[PublicService, Depends(get_service)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/profile", response_model=ProfileOut)
async def profile(service: Service) -> ProfileOut:
    return await service.profile()


@router.get("/posts", response_model=Page[PostSummary])
async def posts(
    service: Service,
    page: PageNumber = 1,
    page_size: PageSize = 10,
    tag: Annotated[str | None, Query(max_length=100)] = None,
    featured: bool | None = None,
    year: Annotated[int | None, Query(ge=1, le=9998)] = None,
) -> Page[PostSummary]:
    return await service.posts(page, page_size, tag, featured, year)


@router.get("/posts/{slug}", response_model=PostDetail)
async def post(slug: str, service: Service) -> PostDetail:
    return await service.post(slug)


@router.get("/projects", response_model=Page[ProjectOut])
async def projects(
    service: Service,
    page: PageNumber = 1,
    page_size: PageSize = 10,
    featured: bool | None = None,
    status: Literal["active", "completed", "archived", "experimental"] | None = None,
) -> Page[ProjectOut]:
    return await service.projects(page, page_size, featured, status)


@router.get("/projects/{slug}", response_model=ProjectOut)
async def project(slug: str, service: Service) -> ProjectOut:
    return await service.project(slug)


@router.get("/tags", response_model=list[TagOut])
async def tags(service: Service) -> list[TagOut]:
    return await service.tags()
