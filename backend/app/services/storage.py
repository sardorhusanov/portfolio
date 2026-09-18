import io
import logging
import warnings
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import Post, Profile, Project, Upload

Image.MAX_IMAGE_PIXELS = 32_000_000
log = logging.getLogger(__name__)


class Storage(Protocol):
    async def write(self, key: str, data: bytes) -> None: ...
    async def delete(self, key: str) -> None: ...
    def url(self, key: str) -> str: ...


class LocalStorage:
    def __init__(self, root: Path | None = None):
        self.root = (root or get_settings().upload_dir).resolve()

    def path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise AppError("Invalid storage path.", 422)
        return path

    async def write(self, key: str, data: bytes) -> None:
        path = self.path(key)
        await run_in_threadpool(path.parent.mkdir, parents=True, exist_ok=True)
        await run_in_threadpool(path.write_bytes, data)

    async def delete(self, key: str) -> None:
        await run_in_threadpool(self.path(key).unlink, missing_ok=True)

    def url(self, key: str) -> str:
        return "/uploads/" + key


def optimize(data: bytes, declared: str) -> tuple[bytes, bytes, int, int]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if Image.MIME.get(source.format) != declared:
                    raise AppError("The file content does not match its image type.", 422)
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGBA")
                image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                # Strip EXIF, ICC, and arbitrary metadata by copying pixels into a fresh image.
                clean = Image.new("RGBA", image.size)
                clean.paste(image)
                webp = io.BytesIO()
                clean.save(webp, "WEBP", quality=88, method=4)
                rgb = Image.new("RGB", clean.size, "white")
                rgb.paste(clean, mask=clean.getchannel("A"))
                jpeg = io.BytesIO()
                rgb.save(jpeg, "JPEG", quality=90, optimize=True)
                return webp.getvalue(), jpeg.getvalue(), clean.width, clean.height
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise AppError(
            "This image could not be decoded safely. Choose a JPEG, PNG, or WebP image.", 422
        ) from None


class StorageService:
    def __init__(self, session: AsyncSession, storage: Storage | None = None):
        self.session = session
        self.storage = storage or LocalStorage()

    async def upload(self, file: UploadFile, folder: str) -> Upload:
        types = {"image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}, "image/webp": {".webp"}}
        suffix = Path(file.filename or "").suffix.lower()
        if file.content_type not in types or suffix not in types[file.content_type]:
            raise AppError("Upload a JPEG, PNG, or WebP image with a matching file extension.", 422)
        limit = get_settings().max_image_upload_mb * 1024 * 1024
        data = await file.read(limit + 1)
        await file.close()
        if len(data) > limit:
            raise AppError("This image exceeds the upload size limit.", 413)
        webp, jpeg, width, height = await run_in_threadpool(optimize, data, file.content_type)
        stem = f"{folder}/{uuid4().hex}"
        key = stem + ".webp"
        await self.storage.write(key, webp)
        try:
            await self.storage.write(stem + ".jpg", jpeg)
            upload = Upload(
                storage_key=key,
                url=self.storage.url(key),
                original_name=Path((file.filename or "image").replace("\\", "/")).name[:255],
                media_type="image/webp",
                size=len(webp),
                width=width,
                height=height,
            )
            self.session.add(upload)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self.storage.delete(key)
            await self.storage.delete(stem + ".jpg")
            raise
        log.info("image_upload_success", extra={"upload_id": str(upload.id)})
        return upload

    async def delete(self, upload_id: UUID) -> None:
        upload = await self.session.get(Upload, upload_id)
        if not upload:
            raise AppError("Image not found.", 404)
        # Never delete an image still used by public or private content.
        post = await self.session.scalar(
            select(Post.id)
            .where(
                or_(
                    Post.cover_image_url == upload.url,
                    Post.content_html.contains(upload.url, autoescape=True),
                )
            )
            .limit(1)
        )
        project = await self.session.scalar(
            select(Project.id).where(Project.cover_image_url == upload.url).limit(1)
        )
        profile = await self.session.scalar(
            select(Profile.id).where(Profile.avatar_url == upload.url).limit(1)
        )
        if post or project or profile:
            raise AppError(
                "This image is still used by content. Remove those references first.", 409
            )
        await self.storage.delete(upload.storage_key)
        await self.storage.delete(upload.storage_key[:-5] + ".jpg")
        await self.session.delete(upload)
        await self.session.commit()
