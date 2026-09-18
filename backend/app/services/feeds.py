from email.utils import format_datetime
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

from app.core.config import get_settings
from app.repositories.public import PublicRepository


class FeedService:
    def __init__(self, repository: PublicRepository) -> None:
        self.repository = repository
        self.base = get_settings().site_url.rstrip("/")

    async def sitemap(self) -> bytes:
        root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for path in ["/", "/projects", "/writing", "/about"]:
            SubElement(SubElement(root, "url"), "loc").text = self.base + path
        for slug, updated in await self.repository.sitemap_posts():
            url = SubElement(root, "url")
            SubElement(url, "loc").text = f"{self.base}/writing/{slug}"
            SubElement(url, "lastmod").text = updated.isoformat()
        return tostring(root, encoding="utf-8", xml_declaration=True)

    async def rss(self) -> bytes:
        root = Element("rss", version="2.0")
        channel = SubElement(root, "channel")
        profile = await self.repository.profile()
        SubElement(channel, "title").text = f"{profile.name if profile else 'Portfolio'} — Writing"
        SubElement(channel, "link").text = self.base + "/writing"
        SubElement(
            channel, "description"
        ).text = "Notes on backend engineering and useful software."
        for post in await self.repository.feed_posts():
            item = SubElement(channel, "item")
            SubElement(item, "title").text = post.title
            link = urljoin(self.base + "/", "writing/" + post.slug)
            SubElement(item, "link").text = link
            SubElement(item, "guid", isPermaLink="true").text = link
            SubElement(item, "description").text = post.excerpt or ""
            if profile:
                SubElement(item, "{http://purl.org/dc/elements/1.1/}creator").text = profile.name
            SubElement(item, "pubDate").text = format_datetime(post.published_at)
        return tostring(root, encoding="utf-8", xml_declaration=True)
