"""Render the supported Tiptap schema on the server, then sanitize the result."""

import json
import re
from html import escape
from typing import Any
from urllib.parse import urlparse

from app.core.content import TextExtractor, sanitize_html
from app.core.errors import AppError


def safe_url(value: str, image: bool = False) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Invalid URL")
    parsed = urlparse(value)
    if value.startswith("/") and not value.startswith("//") and "\\" not in value:
        return value
    if parsed.scheme in ({"http", "https"} if image else {"http", "https", "mailto"}):
        if parsed.scheme == "mailto" or parsed.netloc:
            return value
    raise ValueError("Use an HTTP(S) URL or a local image URL.")


def plain_text(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def excerpt_from(html: str) -> str:
    text = plain_text(html)
    return text if len(text) <= 220 else text[:217].rsplit(" ", 1)[0] + "…"


def render_document(document: dict[str, Any]) -> str:
    if document.get("type") != "doc" or len(json.dumps(document)) > 2_000_000:
        raise AppError("Invalid or oversized article document.", 422)
    nodes = 0

    def render(node: dict[str, Any], depth: int = 0) -> str:
        nonlocal nodes
        nodes += 1
        if nodes > 20000 or depth > 32 or not isinstance(node, dict):
            raise ValueError("Article is too complex")
        kind = node.get("type")
        attrs = node.get("attrs") or {}
        if not isinstance(attrs, dict):
            raise ValueError("Invalid attributes")
        if kind == "text":
            if not isinstance(node.get("text"), str):
                raise ValueError("Invalid text")
            value = escape(node["text"])
            for mark in node.get("marks", []):
                tag = {
                    "bold": "strong",
                    "italic": "em",
                    "strike": "s",
                    "code": "code",
                    "underline": "u",
                }.get(mark.get("type"))
                if tag:
                    value = f"<{tag}>{value}</{tag}>"
                elif mark.get("type") == "link":
                    href = escape(safe_url((mark.get("attrs") or {}).get("href", "")), quote=True)
                    value = f'<a href="{href}">{value}</a>'
                else:
                    raise ValueError("Unsupported text formatting")
            return value
        if kind == "image":
            src = escape(safe_url(attrs.get("src", ""), image=True), quote=True)
            alt = escape(str(attrs.get("alt") or "")[:300], quote=True)
            return f'<img src="{src}" alt="{alt}" />'
        if kind in {"horizontalRule", "hardBreak"}:
            return "<hr />" if kind == "horizontalRule" else "<br />"
        children = node.get("content", [])
        if not isinstance(children, list):
            raise ValueError("Invalid content")
        inner = "".join(render(child, depth + 1) for child in children)
        tags = {
            "doc": "",
            "paragraph": "p",
            "bulletList": "ul",
            "orderedList": "ol",
            "listItem": "li",
            "blockquote": "blockquote",
            "table": "table",
            "tableRow": "tr",
            "tableHeader": "th",
            "tableCell": "td",
        }
        if kind == "heading":
            level = attrs.get("level", 2)
            if level not in [1, 2, 3]:
                raise ValueError("Use heading levels 1–3")
            tag = f"h{level}"
        elif kind == "codeBlock":
            language = str(attrs.get("language") or "plaintext")
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,30}", language):
                language = "plaintext"
            # Marks are irrelevant inside code; escape their plain text instead.
            code = "".join(str(child.get("text", "")) for child in children)
            return f'<pre><code class="language-{language}">{escape(code)}</code></pre>'
        elif kind in tags:
            tag = tags[kind]
        else:
            raise ValueError("Unsupported editor node")
        if not tag:
            return inner
        extra = ""
        if kind == "orderedList":
            extra = f' start="{max(1, min(int(attrs.get("start", 1)), 10000))}"'
        if kind in {"tableHeader", "tableCell"}:
            extra = "".join(
                f' {key}="{max(1, min(int(attrs.get(key, 1)), 20))}"'
                for key in ["colspan", "rowspan"]
            )
        return f"<{tag}{extra}>{inner}</{tag}>"

    try:
        return sanitize_html(render(document))
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise AppError("The article contains unsupported or invalid content.", 422) from None
