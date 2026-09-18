import ipaddress
import re
from html import escape
from urllib.parse import quote, urljoin, urlparse

from app.core.config import get_settings
from app.db.models import Post
from app.integrations.telegram.exceptions import TelegramError
from app.services.editor import excerpt_from


def public_base() -> str:
    base = get_settings().site_url.rstrip("/")
    url = urlparse(base)
    host = url.hostname or ""
    try:
        private = not ipaddress.ip_address(host).is_global
    except ValueError:
        private = host in {"localhost", "localhost.localdomain"} or host.endswith(
            (".local", ".localhost")
        )
    if url.scheme != "https" or private or not host:
        raise TelegramError(
            "Set PUBLIC_SITE_URL to your public HTTPS website before synchronizing Telegram."
        )
    return base


def trim(value: str, units: int) -> str:
    # Telegram limits use UTF-16 units; never split a surrogate pair or HTML entity.
    out = []
    length = 0
    for char in value:
        cost = 2 if ord(char) > 0xFFFF else 1
        if length + cost > units:
            break
        out.append(char)
        length += cost
    result = "".join(out)
    if len(result) < len(value):
        result = result.rsplit(" ", 1)[0] if " " in result[-25:] else result
        result += "…"
    return result


def announcement(post: Post, preview: bool = False) -> str:
    link = (
        (get_settings().site_url.rstrip("/") if preview else public_base())
        + "/writing/"
        + quote(post.slug, safe="-")
    )
    title = escape(trim(post.title, 180))
    excerpt = escape(trim(post.excerpt or excerpt_from(post.content_html), 330))
    tags = " ".join(
        "#" + re.sub(r"[^a-zA-Z0-9_]", "", tag.slug.replace("-", "_")) for tag in post.tags[:4]
    )
    topics = "\n\n" + escape(trim(tags, 80)) if tags else ""
    # Under 650 visible UTF-16 units, safe for both 1024 captions and 4096 text.
    return (
        f"<b>{title}</b>\n\n{excerpt}{topics}\n\n"
        f'<a href="{escape(link, quote=True)}">Read the full article →</a>'
    )


def cover_url(post: Post) -> str | None:
    if not post.cover_image_url:
        return None
    cover = post.cover_image_url
    if cover.startswith("/uploads/") and cover.endswith(".webp"):
        cover = cover[:-5] + ".jpg"
    if cover.startswith("/covers/") and cover.endswith(".svg"):
        cover = cover[:-4] + ".png"
    return urljoin(public_base() + "/", cover)
