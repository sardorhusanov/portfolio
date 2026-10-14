"""Public, durable image storage for Vercel Functions."""

import logging
import re

from vercel.blob import AsyncBlobClient

from app.core.config import get_settings
from app.core.errors import AppError

log = logging.getLogger(__name__)


class VercelBlobStorage:
    def __init__(self):
        self._token = get_settings().blob_read_write_token.get_secret_value()
        # The SDK response is the authority for the public URL; never derive it from a token.
        self._urls: dict[str, str] = {}

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or any(
            part in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
            for part in key.split("/")
        ):
            raise AppError("Invalid storage path.", 422)

    async def write(self, key: str, data: bytes) -> None:
        self._validate_key(key)
        media_type = "image/webp" if key.endswith(".webp") else "image/jpeg"
        try:
            async with AsyncBlobClient(token=self._token) as client:
                blob = await client.put(
                    key,
                    data,
                    access="public",
                    content_type=media_type,
                    # Keys already include a UUID. Matching WebP/JPEG names are required
                    # by Telegram's image fallback, so never add an independent suffix.
                    add_random_suffix=False,
                    overwrite=False,
                    cache_control_max_age=31536000,
                )
                self._urls[key] = blob.url
        except Exception as exc:
            # SDK/network errors may include request details. Expose neither those nor tokens.
            log.error("blob_write_failed", extra={"error_type": type(exc).__name__})
            raise AppError("Image storage is temporarily unavailable. Try again later.", 503) from None

    async def delete(self, key: str) -> None:
        self._validate_key(key)
        try:
            async with AsyncBlobClient(token=self._token) as client:
                # Pathnames work across requests without retrieving or reconstructing the URL.
                await client.delete(key)
            self._urls.pop(key, None)
        except Exception as exc:
            log.error("blob_delete_failed", extra={"error_type": type(exc).__name__})
            raise AppError("Image storage is temporarily unavailable. Try again later.", 503) from None

    def url(self, key: str) -> str:
        """Return the SDK URL after this storage instance successfully writes the key."""
        self._validate_key(key)
        if key not in self._urls:
            raise AppError("This image has not been uploaded.", 422)
        return self._urls[key]
