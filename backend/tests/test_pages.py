from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models import Post
from app.main import app
from app.services import pages


@pytest.mark.asyncio
async def test_crawlable_metadata_and_real_404(client, session, tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text(
        '<html><head><title>Default</title><meta name="description" content="Default" />'
        '</head><body><div id="root"></div></body></html>'
    )
    monkeypatch.setattr(pages, "DIST", tmp_path)
    from app.api.routes import pages as page_routes

    monkeypatch.setattr(page_routes, "DIST", tmp_path)
    session.add_all(
        [
            Post(
                title='Transactions & "safety"',
                slug="transactions",
                excerpt="A <careful> look.",
                content_html="<p>Safe content</p>",
                status="published",
                published_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
                cover_image_url="/covers/transactions.svg",
            ),
            Post(title="Private title", slug="draft", status="draft", content_html="Private body"),
        ]
    )
    await session.commit()
    response = await client.get("/writing/transactions")
    assert response.status_code == 200
    assert "<title>Transactions &amp; &quot;safety&quot;" in response.text
    assert 'property="og:type" content="article"' in response.text
    assert "transactions.png" in response.text
    assert response.text.count("<title>") == 1
    assert "&lt;careful&gt;" in response.text
    for path in ["/writing/draft", "/missing", "/writing/missing"]:
        response = await client.get(path)
        assert response.status_code == 404
        assert 'content="noindex, follow"' in response.text
        assert "Private title" not in response.text and "Private body" not in response.text
    assert (await client.get("/api/v1/nonexistent")).status_code == 404
    assert (await client.get("/profile")).status_code == 404


@pytest.mark.asyncio
async def test_cors_is_restricted():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        allowed = await client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
        other = await client.get("/health", headers={"Origin": "https://unrelated.example"})
        assert "access-control-allow-origin" not in other.headers
