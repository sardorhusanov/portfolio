from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.core.config import get_settings


class BodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        limit = (
            (get_settings().max_image_upload_mb * 1024 * 1024 + 65536)
            if path.endswith("/uploads/images")
            else 2_500_000
        )
        headers = dict(scope.get("headers", []))
        try:
            size = int(headers.get(b"content-length", b"0"))
        except ValueError:
            size = limit + 1
        if size > limit:
            return await JSONResponse(
                {"detail": "Request exceeds the upload size limit."}, status_code=413
            )(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise HTTPException(413, "Request exceeds the upload size limit.")
            return message

        async def private_send(message):
            if message["type"] == "http.response.start" and path.startswith(
                ("/api/v1/admin", "/admin")
            ):
                message["headers"] = [
                    (k, v) for k, v in message["headers"] if k.lower() != b"cache-control"
                ] + [(b"cache-control", b"no-store"), (b"x-robots-tag", b"noindex, nofollow")]
            await send(message)

        await self.app(scope, bounded_receive, private_send)
