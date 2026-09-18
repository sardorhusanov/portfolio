from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.content import reading_time, sanitize_html, slugify
from app.db.models import Post, Project, Tag


async def add_content(session):
    python = Tag(name="Python", slug="python")
    private = Tag(name="Private planning", slug="private")
    now = datetime.now(timezone.utc)
    for index in range(4):
        session.add(
            Post(
                title=f"Published note {index}",
                slug=f"note-{index}",
                content_html="<p>Public text</p>",
                status="published",
                featured=index == 0,
                published_at=now - timedelta(days=index + 1),
                tags=[python],
            )
        )
    session.add_all(
        [
            Post(
                title="Secret draft",
                slug="secret",
                status="draft",
                content_html="<p>secret</p>",
                tags=[private],
            ),
            Post(
                title="Archived",
                slug="archived",
                status="archived",
                content_html="",
                published_at=now,
            ),
            Post(
                title="Scheduled",
                slug="future",
                status="published",
                content_html="",
                published_at=now + timedelta(days=10),
                tags=[private],
            ),
        ]
    )
    await session.commit()


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_pagination_and_privacy(client, session):
    await add_content(session)
    result = (await client.get("/api/v1/posts?page_size=2")).json()
    assert (result["total"], result["pages"], result["page"]) == (4, 2, 1)
    assert [p["slug"] for p in result["items"]] == ["note-0", "note-1"]
    second = (await client.get("/api/v1/posts?page_size=2&page=2")).json()
    assert [p["slug"] for p in second["items"]] == ["note-2", "note-3"]
    assert (await client.get("/api/v1/posts?page=99")).json()["items"] == []
    for slug in ["secret", "archived", "future", "missing"]:
        assert (await client.get(f"/api/v1/posts/{slug}")).status_code == 404
    detail = (await client.get("/api/v1/posts/note-1")).json()
    assert detail["previous"]["slug"] == "note-2"
    assert detail["next"]["slug"] == "note-0"
    assert "content_json" not in detail and "telegram_message_id" not in detail
    assert (await client.get("/api/v1/posts/note-0")).json()["next"] is None
    assert (await client.get("/api/v1/posts/note-3")).json()["previous"] is None


@pytest.mark.asyncio
async def test_filters_and_public_tags(client, session):
    await add_content(session)
    assert (await client.get("/api/v1/posts?tag=python")).json()["total"] == 4
    assert (await client.get("/api/v1/posts?featured=true")).json()["total"] == 1
    assert (await client.get("/api/v1/posts?featured=false")).json()["total"] == 3
    assert (await client.get("/api/v1/posts?tag=private")).json()["total"] == 0
    assert (await client.get("/api/v1/posts?year=2000")).json()["total"] == 0
    year = (datetime.now(timezone.utc) - timedelta(days=1)).year
    assert (await client.get(f"/api/v1/posts?year={year}&featured=true")).json()["total"] == 1
    assert [t["slug"] for t in (await client.get("/api/v1/tags")).json()] == ["python"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query", ["page=0", "page=-1", "page_size=101", "page_size=0", "year=10000", "featured=maybe"]
)
async def test_query_validation(client, query):
    assert (await client.get("/api/v1/posts?" + query)).status_code == 422


@pytest.mark.asyncio
async def test_projects(client, session):
    for name, order, status, featured in [
        ("Second", 2, "archived", False),
        ("First", 1, "active", True),
    ]:
        session.add(
            Project(
                name=name,
                slug=name.lower(),
                short_description="A useful application",
                display_order=order,
                status=status,
                featured=featured,
                technologies=["Python"],
            )
        )
    await session.commit()
    response = (await client.get("/api/v1/projects")).json()
    assert [p["slug"] for p in response["items"]] == ["first", "second"]
    assert (await client.get("/api/v1/projects?featured=true&status=active")).json()["total"] == 1
    assert (await client.get("/api/v1/projects?status=invalid")).status_code == 422
    assert (await client.get("/api/v1/projects/first")).json()["name"] == "First"
    assert (await client.get("/api/v1/projects/missing")).status_code == 404
    assert (await client.get("/api/v1/projects?page_size=1&page=2")).json()["items"][0][
        "slug"
    ] == "second"


@pytest.mark.asyncio
async def test_feeds_hide_private_content(client, session):
    await add_content(session)
    for path in ["/sitemap.xml", "/rss.xml"]:
        response = await client.get(path)
        assert response.status_code == 200
        ElementTree.fromstring(response.text)
        assert "note-0" in response.text
        assert (
            "secret" not in response.text
            and "future" not in response.text
            and "archived" not in response.text
        )
    assert "Sitemap:" in (await client.get("/robots.txt")).text


@pytest.mark.asyncio
async def test_content_hooks_and_unique_slugs(session):
    post = Post(
        title="A useful article!",
        content_html="<p>" + "word " * 201 + "</p><script>alert(1)</script>",
    )
    session.add(post)
    await session.commit()
    assert post.slug == "a-useful-article" and post.reading_time_minutes == 2
    assert "script" not in post.content_html
    post.content_html = "<p>Shorter now.</p>"
    await session.commit()
    assert post.reading_time_minutes == 1
    async with session.begin_nested():
        session.add(Post(title="A useful article!", content_html=""))
        with pytest.raises(IntegrityError):
            await session.flush()
    assert (await session.scalar(select(Post).where(Post.slug == post.slug))).id == post.id


def test_html_and_slug_utilities():
    assert slugify("How PostgreSQL Transactions Work") == "how-postgresql-transactions-work"
    assert reading_time("<p>hello</p>") == 1
    cleaned = sanitize_html(
        '<img src="x" onerror="alert(1)"><a href="javascript:alert(1)">bad</a>'
        '<script>evil()</script><pre><code class="language-python">print(1)</code></pre>'
    )
    assert "onerror" not in cleaned and "javascript:" not in cleaned and "evil" not in cleaned
    assert 'class="language-python"' in cleaned
