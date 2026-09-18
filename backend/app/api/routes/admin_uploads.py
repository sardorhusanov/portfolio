from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.api.admin_dependencies import get_admin
from app.api.dependencies import Session
from app.core.rate_limit import limiter
from app.schemas.admin import UploadOut
from app.services.storage import StorageService

router = APIRouter(
    prefix="/api/v1/admin/uploads", tags=["Uploads"], dependencies=[Depends(get_admin)]
)


@router.post("/images", response_model=UploadOut, status_code=201)
async def upload(
    session: Session,
    file: UploadFile = File(),
    folder: Literal["posts", "projects", "profile"] = Form(default="posts"),
):
    limiter.check("uploads", 30)
    return UploadOut.model_validate(await StorageService(session).upload(file, folder))


@router.delete("/{upload_id}", status_code=204)
async def delete(upload_id: UUID, session: Session):
    await StorageService(session).delete(upload_id)
    return Response(status_code=204)
