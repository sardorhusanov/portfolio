import io

import pytest
import pytest_asyncio
from PIL import Image

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import password_hasher
from app.db.models import Admin
from app.integrations.telegram.client import TelegramClient
from app.integrations.telegram.exceptions import TelegramError

CSRF = {"Origin": "http://localhost:5173", "X-CSRF-Protection": "1"}
DOCUMENT = {
    "type": "doc",
    "content": [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Useful notes"}],
        },
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "A useful article about reliable systems.",
                    "marks": [{"type": "bold"}],
                }
            ],
        },
        {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [{"type": "text", "text": "print('hello')"}],
        },
    ],
}


@pytest_asyncio.fixture(autouse=True)
async def reset_limits():
    limiter.buckets.clear()


@pytest_asyncio.fixture
async def credentials(session):
    admin = Admin(
        email="owner@example.com", hashed_password=password_hasher.hash("a-long-test-password")
    )
    session.add(admin)
    await session.commit()
    return {"email": admin.email, "password": "a-long-test-password"}


@pytest_asyncio.fixture
async def authenticated(client, credentials):
    response = await client.post("/api/v1/admin/auth/login", json=credentials, headers=CSRF)
    assert response.status_code == 200, response.text
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    return client


@pytest.fixture
def telegram(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "telegram_bot_token", "test-token-never-used-on-network")
    monkeypatch.setattr(settings, "telegram_channel_id", "@test_channel")
    monkeypatch.setattr(settings, "site_url", "https://portfolio.example")
    calls = []
    failures = []

    async def call(self, method, payload):
        calls.append((method, payload))
        if failures:
            raise failures.pop(0)
        return {"message_id": 123, "chat": {"id": -100123}}

    monkeypatch.setattr(TelegramClient, "call", call)
    return calls, failures


async def create_post(client, **extra):
    response = await client.post(
        "/api/v1/admin/posts", json={"title": "A useful note", "content_json": DOCUMENT, **extra}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def publish(client, post):
    response = await client.post(
        f"/api/v1/admin/posts/{post['id']}/publish", json={"revision": post["revision"]}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_login_rotation_reuse_logout(client, credentials):
    assert (await client.get("/api/v1/admin/posts")).status_code == 401
    assert (await client.post("/api/v1/admin/auth/login", json=credentials)).status_code == 403
    invalid = await client.post(
        "/api/v1/admin/auth/login", json={**credentials, "password": "wrong"}, headers=CSRF
    )
    unknown = await client.post(
        "/api/v1/admin/auth/login",
        json={**credentials, "email": "missing@example.com"},
        headers=CSRF,
    )
    assert invalid.status_code == unknown.status_code == 401
    assert invalid.json() == unknown.json()
    response = await client.post("/api/v1/admin/auth/login", json=credentials, headers=CSRF)
    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    assert "portfolio_refresh" not in response.json()
    old_cookie = client.cookies.get("portfolio_refresh")
    access = response.json()["access_token"]
    assert (
        await client.get("/api/v1/admin/auth/me", headers={"Authorization": "Bearer " + access})
    ).status_code == 200
    rotated = await client.post("/api/v1/admin/auth/refresh", headers=CSRF)
    assert rotated.status_code == 200
    assert client.cookies.get("portfolio_refresh") != old_cookie
    reused = await client.post(
        "/api/v1/admin/auth/refresh", headers={**CSRF, "Cookie": "portfolio_refresh=" + old_cookie}
    )
    assert reused.status_code == 401
    assert (
        await client.get("/api/v1/admin/auth/me", headers={"Authorization": "Bearer " + access})
    ).status_code == 401
    response = await client.post("/api/v1/admin/auth/login", json=credentials, headers=CSRF)
    access = response.json()["access_token"]
    assert (await client.post("/api/v1/admin/auth/logout", headers=CSRF)).status_code == 204
    assert (
        await client.get("/api/v1/admin/auth/me", headers={"Authorization": "Bearer " + access})
    ).status_code == 401


async def test_posts_drafts_updates_publish_archive(authenticated, session, telegram):
    client = authenticated
    post = await create_post(client, tags=["Python", "python", "PYTHON"])
    assert post["status"] == "draft" and len(post["tags"]) == 1
    assert (await client.get("/api/v1/posts/a-useful-note")).status_code == 404
    assert "<strong>" in post["content_html"] and "language-python" in post["content_html"]
    updated = await client.patch(
        f"/api/v1/admin/posts/{post['id']}",
        json={"revision": post["revision"], "title": "Updated note", "autosave": True},
    )
    assert updated.status_code == 200, updated.text
    post = updated.json()
    assert post["last_autosaved_at"]
    conflict = await client.patch(
        f"/api/v1/admin/posts/{post['id']}", json={"revision": 1, "title": "Lost changes"}
    )
    assert conflict.status_code == 409
    post = await publish(client, post)
    original_publication = post["published_at"]
    assert post["telegram_message_id"] == "123" and post["telegram_sync_status"] == "synced"
    assert (await client.get("/api/v1/posts/a-useful-note")).status_code == 200
    # Repeated publish never sends another announcement, including stale repeated requests.
    await publish(client, post)
    calls, _ = telegram
    assert [method for method, _ in calls] == ["sendMessage", "editMessageText"]
    changed = await client.patch(
        f"/api/v1/admin/posts/{post['id']}",
        json={"revision": post["revision"], "slug": "updated-url", "content_json": DOCUMENT},
    )
    assert changed.status_code == 200, changed.text
    post = changed.json()
    assert post["published_at"] == original_publication
    assert calls[-1][0] == "editMessageText" and "/updated-url" in calls[-1][1]["text"]
    assert (await client.get("/api/v1/posts/a-useful-note")).json()["slug"] == "updated-url"
    redirected = await client.get("/writing/a-useful-note")
    assert (
        redirected.status_code == 301 and redirected.headers["location"] == "/writing/updated-url"
    )
    reserved = await client.post(
        "/api/v1/admin/posts",
        json={"title": "Collision", "slug": "a-useful-note", "content_json": DOCUMENT},
    )
    assert reserved.status_code == 409
    archived = await client.post(
        f"/api/v1/admin/posts/{post['id']}/archive", json={"revision": post["revision"]}
    )
    assert archived.status_code == 200
    assert archived.json()["telegram_message_id"] == "123"
    for slug in ["updated-url", "a-useful-note"]:
        assert (await client.get("/api/v1/posts/" + slug)).status_code == 404
    assert "updated-url" not in (await client.get("/sitemap.xml")).text
    assert "updated-url" not in (await client.get("/feed.xml")).text


async def test_photo_edits_keep_original_media(authenticated, telegram):
    post = await create_post(authenticated, cover_image_url="https://portfolio.example/cover.jpg")
    post = await publish(authenticated, post)
    assert post["telegram_message_type"] == "photo"
    changed = await authenticated.patch(
        f"/api/v1/admin/posts/{post['id']}",
        json={"revision": post["revision"], "cover_image_url": "https://portfolio.example/new.jpg"},
    )
    assert changed.status_code == 200, changed.text
    calls, failures = telegram
    assert [method for method, _ in calls] == ["sendPhoto", "editMessageCaption"]
    assert "photo" not in calls[-1][1]
    failures.append(TelegramError("Already current", not_modified=True))
    retried = await authenticated.post(f"/api/v1/admin/posts/{post['id']}/telegram/sync")
    assert retried.json()["telegram_sync_status"] == "synced"
    assert all(
        payload["message_id"] == 123 for method, payload in calls if method.startswith("edit")
    )


async def test_failure_retry_and_ambiguous_send(authenticated, telegram):
    calls, failures = telegram
    failures.append(TelegramError("Permission denied"))
    post = await publish(authenticated, await create_post(authenticated))
    assert post["status"] == "published" and post["telegram_sync_status"] == "failed"
    assert (await authenticated.get("/api/v1/posts/" + post["slug"])).status_code == 200
    retry = await authenticated.post(f"/api/v1/admin/posts/{post['id']}/telegram/sync")
    assert retry.status_code == 200 and retry.json()["telegram_sync_status"] == "synced"
    uncertain = await create_post(authenticated, title="Uncertain delivery")
    failures.append(TelegramError("Check delivery", uncertain=True))
    uncertain = await publish(authenticated, uncertain)
    before = len(calls)
    assert uncertain["telegram_delivery_uncertain"] is True
    assert (
        await authenticated.post(f"/api/v1/admin/posts/{uncertain['id']}/telegram/sync")
    ).status_code == 409
    assert len(calls) == before
    # Saving the website still succeeds when sending requires manual reconciliation.
    updated = await authenticated.patch(
        f"/api/v1/admin/posts/{uncertain['id']}",
        json={"revision": uncertain["revision"], "title": "Still saved"},
    )
    assert updated.status_code == 200 and updated.json()["title"] == "Still saved"
    recreated = await authenticated.post(
        f"/api/v1/admin/posts/{uncertain['id']}/telegram/recreate", json={"confirm": True}
    )
    assert recreated.status_code == 200 and recreated.json()["telegram_sync_status"] == "synced"
    assert len(calls) == before + 1


async def test_missing_message_requires_explicit_recreation(authenticated, telegram):
    calls, failures = telegram
    post = await publish(authenticated, await create_post(authenticated))
    failures.append(TelegramError("The Telegram message no longer exists.", missing=True))
    assert (await authenticated.post(f"/api/v1/admin/posts/{post['id']}/telegram/sync")).json()[
        "telegram_sync_status"
    ] == "failed"
    count = len(calls)
    assert (
        await authenticated.post(f"/api/v1/admin/posts/{post['id']}/telegram/sync")
    ).status_code == 409
    assert len(calls) == count
    assert (
        await authenticated.post(
            f"/api/v1/admin/posts/{post['id']}/telegram/recreate", json={"confirm": True}
        )
    ).status_code == 200
    assert calls[-1][0] == "sendMessage"


async def test_publish_validation_and_safe_rendering(authenticated):
    empty = await create_post(authenticated, content_json={"type": "doc", "content": []})
    assert (
        await authenticated.post(
            f"/api/v1/admin/posts/{empty['id']}/publish", json={"revision": empty["revision"]}
        )
    ).status_code == 422
    evil = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "<script>alert(1)</script>",
                        "marks": [{"type": "link", "attrs": {"href": "javascript:alert(1)"}}],
                    }
                ],
            }
        ],
    }
    assert (
        await authenticated.post(
            "/api/v1/admin/posts", json={"title": "Unsafe", "content_json": evil}
        )
    ).status_code == 422
    assert (
        await authenticated.post(
            "/api/v1/admin/posts", json={"title": "Untrusted", "content_html": "<p>Ignore me</p>"}
        )
    ).status_code == 422
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "word " * 401 + "<script>alert(1)</script>"}],
            }
        ],
    }
    post = await create_post(authenticated, title="Long safe note", content_json=doc)
    assert post["reading_time_minutes"] == 3
    assert "<script>" not in post["content_html"] and "&lt;script&gt;" in post["content_html"]


async def test_project_management_profile_and_reordering(authenticated):
    client = authenticated
    first = await client.post(
        "/api/v1/admin/projects",
        json={
            "name": "Useful API",
            "short_description": "A project",
            "technologies": ["Python"],
            "featured": True,
        },
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        "/api/v1/admin/projects", json={"name": "Second API", "short_description": "Another"}
    )
    a, b = first.json(), second.json()
    assert (
        await client.put("/api/v1/admin/projects/reorder", json={"ids": [b["id"], a["id"]]})
    ).status_code == 200
    assert (await client.get("/api/v1/projects")).json()["items"][0]["id"] == b["id"]
    profile = {
        "name": "Sardorbek",
        "headline": "Backend Engineer",
        "short_bio": "Building",
        "long_bio": "My story",
        "location": "Tashkent",
        "currently_building": "CMS",
        "currently_learning": "Systems",
        "skills": {"Backend": ["Python"]},
    }
    assert (await client.put("/api/v1/admin/profile", json=profile)).status_code == 200
    assert (await client.get("/api/v1/profile")).json()["currently_building"] == "CMS"
    assert (
        await client.request("DELETE", "/api/v1/admin/projects/" + a["id"], json={"confirm": True})
    ).status_code == 204


async def test_image_upload_security_and_metadata(authenticated, client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path)
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), "green").save(buf, "PNG")
    image = buf.getvalue()
    result = await authenticated.post(
        "/api/v1/admin/uploads/images",
        files={"file": ("../../evil.png", image, "image/png")},
        data={"folder": "posts"},
    )
    assert result.status_code == 201, result.text
    data = result.json()
    assert data["url"].startswith("/uploads/posts/") and ".." not in data["url"]
    assert data["original_name"] == "evil.png" and data["media_type"] == "image/webp"
    assert (data["width"], data["height"]) == (40, 30)
    assert len(list((tmp_path / "posts").iterdir())) == 2
    for filename, payload, mime in [
        ("evil.svg", b"<svg/>", "image/svg+xml"),
        ("fake.png", b"not an image", "image/png"),
        ("wrong.jpg", image, "image/jpeg"),
    ]:
        assert (
            await authenticated.post(
                "/api/v1/admin/uploads/images", files={"file": (filename, payload, mime)}
            )
        ).status_code == 422
    monkeypatch.setattr(get_settings(), "max_image_upload_mb", 1)
    assert (
        await authenticated.post(
            "/api/v1/admin/uploads/images",
            files={"file": ("huge.png", b"x" * 1_100_000, "image/png")},
        )
    ).status_code == 413
    client.headers.pop("Authorization")
    assert (
        await client.post(
            "/api/v1/admin/uploads/images", files={"file": ("test.png", image, "image/png")}
        )
    ).status_code == 401


async def test_protected_endpoints_and_login_rate_limit(client, credentials):
    for path in [
        "/api/v1/admin/overview",
        "/api/v1/admin/profile",
        "/api/v1/admin/projects",
        "/api/v1/admin/posts",
    ]:
        assert (await client.get(path)).status_code == 401
    for _ in range(8):
        assert (
            await client.post(
                "/api/v1/admin/auth/login", headers=CSRF, json={**credentials, "password": "wrong"}
            )
        ).status_code == 401
    assert (
        await client.post("/api/v1/admin/auth/login", headers=CSRF, json=credentials)
    ).status_code == 429
