import math
import re
import unicodedata
from html.parser import HTMLParser

import nh3
from sqlalchemy import event, inspect

from app.db.models import Post, Project, Tag

TAGS = {
    "p",
    "br",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "b",
    "em",
    "i",
    "a",
    "blockquote",
    "ol",
    "ul",
    "li",
    "pre",
    "code",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "s",
    "u",
    "del",
    "figure",
    "figcaption",
}


def sanitize_html(value: str) -> str:
    return nh3.clean(
        value,
        tags=TAGS,
        attributes={
            "ol": {"start"},
            "a": {"href", "title"},
            "img": {"src", "alt", "title", "width", "height"},
            "code": {"class"},
            "th": {"scope", "colspan", "rowspan"},
            "td": {"colspan", "rowspan"},
        },
        url_schemes={"http", "https", "mailto"},
    )


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def reading_time(html: str) -> int:
    parser = TextExtractor()
    parser.feed(html)
    return max(1, math.ceil(len(" ".join(parser.parts).split()) / 200))


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-") or "untitled"


# ORM writes used by the future editor always refresh safe HTML and reading time.
# Bulk SQL bypasses ORM events and must not be used for content writes.
@event.listens_for(Post, "before_insert")
@event.listens_for(Post, "before_update")
def prepare_post(mapper: object, connection: object, target: Post) -> None:
    if not target.slug:
        target.slug = slugify(target.title)
    if inspect(target).attrs.content_html.history.has_changes():
        target.content_html = sanitize_html(target.content_html or "")
        target.reading_time_minutes = reading_time(target.content_html)


@event.listens_for(Project, "before_insert")
@event.listens_for(Tag, "before_insert")
def prepare_named_slug(mapper: object, connection: object, target: Project | Tag) -> None:
    if not target.slug:
        target.slug = slugify(target.name)
