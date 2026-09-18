"""Inject crawlable metadata into Vite's built HTML; React owns the page body."""

import re
from html import escape
from pathlib import Path
from urllib.parse import urljoin

from app.core.config import get_settings
from app.repositories.public import PublicRepository

DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
# backend/app/services -> repository root is parents[3].


class PageService:
    def __init__(self, repository: PublicRepository) -> None:
        self.repository = repository

    async def render(self, path: str) -> tuple[str, int]:
        template = (DIST / "index.html").read_text()
        profile = await self.repository.profile()
        name = profile.name if profile else "Sardorbek Husanov"
        description = (
            profile.short_bio if profile else "Backend engineering, projects, and writing."
        )
        title = f"{name} — {profile.headline if profile else 'Backend Engineer'}"
        image = "/social-preview.png"
        kind = "website"
        status = 200
        titles = {"/": None, "/projects": "Projects", "/writing": "Writing", "/about": "About"}
        admin_page = path == "/admin" or path.startswith("/admin/")
        if admin_page:
            title = f"Admin | {name}"
        elif path in titles:
            if titles[path]:
                title = f"{titles[path]} | {name}"
        elif path.startswith("/writing/"):
            post = await self.repository.post(path.removeprefix("/writing/"))
            if post is None:
                status = 404
            else:
                title = f"{post.seo_title or post.title} | {name}"
                description = post.seo_description or post.excerpt or description
                # SVG covers work in browsers, but social crawlers need the PNG fallback.
                image = post.cover_image_url or image
                if image.endswith(".svg"):
                    image = (
                        image.replace(".svg", ".png")
                        if image.startswith("/covers/")
                        else "/social-preview.png"
                    )
                kind = "article"
        else:
            status = 404
        if status == 404:
            title = f"Page not found | {name}"
            description = "This page could not be found."
        base = get_settings().site_url.rstrip("/") + "/"
        canonical = urljoin(base, path.lstrip("/"))
        image_url = urljoin(base, image)
        template = re.sub(r"<title>.*?</title>", "", template, flags=re.S)
        template = re.sub(r'<meta name="description"[^>]*>', "", template)

        def meta(key: str, value: str, attribute: str = "name") -> str:
            return f'<meta {attribute}="{key}" content="{escape(value, quote=True)}" />'

        head = f"<title>{escape(title)}</title>" + meta("description", description)
        head += f'<link rel="canonical" href="{escape(canonical, quote=True)}" />'
        for key, value in [
            ("og:title", title),
            ("og:description", description),
            ("og:url", canonical),
            ("og:type", kind),
            ("og:image", image_url),
        ]:
            head += meta(key, value, "property")
        for key, value in [
            ("twitter:card", "summary_large_image"),
            ("twitter:title", title),
            ("twitter:description", description),
            ("twitter:image", image_url),
            ("robots", "noindex, follow" if status == 404 or admin_page else "index, follow"),
        ]:
            head += meta(key, value)
        return template.replace("</head>", head + "</head>"), status
