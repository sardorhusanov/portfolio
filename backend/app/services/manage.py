from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.content import slugify
from app.core.errors import AppError
from app.core.exceptions import NotFoundError
from app.db.models import Profile, Project
from app.repositories.admin import AdminRepository
from app.schemas.admin import ProfileInput, ProjectInput


class ManagementService:
    def __init__(self, repository: AdminRepository) -> None:
        self.repo = repository

    async def commit(self) -> None:
        try:
            await self.repo.session.commit()
        except IntegrityError:
            await self.repo.session.rollback()
            raise AppError("That slug is already in use.", 409) from None

    async def project(self, project_id: UUID) -> Project:
        project = await self.repo.project(project_id)
        if not project:
            raise NotFoundError("Project not found.")
        return project

    async def create_project(self, data: ProjectInput) -> Project:
        project = Project(**data.model_dump(exclude={"slug"}), slug=data.slug or slugify(data.name))
        self.repo.session.add(project)
        await self.commit()
        return project

    async def update_project(
        self, project_id: UUID, data: ProjectInput, expected: datetime
    ) -> Project:
        project = await self.repo.project(project_id, lock=True)
        if not project:
            raise NotFoundError("Project not found.")
        if project.updated_at != expected:
            raise AppError("This project has changed. Reload before saving.", 409)
        for key, value in data.model_dump().items():
            setattr(project, key, value if key != "slug" else value or slugify(data.name))
        await self.commit()
        return project

    async def delete_project(self, project_id: UUID) -> None:
        await self.repo.session.delete(await self.project(project_id))
        await self.repo.session.commit()

    async def reorder(self, ids: list[UUID]) -> list[Project]:
        projects = await self.repo.all_projects()
        if len(ids) != len(set(ids)) or set(ids) != {p.id for p in projects}:
            raise AppError("The project list changed. Reload before reordering.", 409)
        lookup = {p.id: p for p in projects}
        for order, project_id in enumerate(ids):
            lookup[project_id].display_order = order
        await self.repo.session.commit()
        return [lookup[pid] for pid in ids]

    async def profile(self) -> Profile:
        profile = await self.repo.profile()
        if not profile:
            raise NotFoundError("Configure a profile to get started.")
        return profile

    async def save_profile(self, data: ProfileInput) -> Profile:
        profile = await self.repo.profile()
        if not profile:
            profile = Profile(id=1, **data.model_dump())
            self.repo.session.add(profile)
        else:
            for key, value in data.model_dump().items():
                setattr(profile, key, value)
        await self.repo.session.commit()
        return profile
