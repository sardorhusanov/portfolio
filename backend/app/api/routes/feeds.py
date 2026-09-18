from fastapi import APIRouter, Response

from app.api.dependencies import Session
from app.core.config import get_settings
from app.repositories.public import PublicRepository
from app.services.feeds import FeedService

router = APIRouter(tags=["discovery"])


@router.get("/sitemap.xml")
async def sitemap(session: Session) -> Response:
    return Response(
        await FeedService(PublicRepository(session)).sitemap(), media_type="application/xml"
    )


@router.get("/feed.xml")
@router.get("/rss.xml", include_in_schema=False)
async def rss(session: Session) -> Response:
    return Response(
        await FeedService(PublicRepository(session)).rss(), media_type="application/rss+xml"
    )


@router.get("/robots.txt")
async def robots() -> Response:
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {get_settings().site_url.rstrip('/')}/sitemap.xml\n",
        media_type="text/plain",
    )
