import asyncio
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Post
from app.integrations.telegram import client as transport
from app.integrations.telegram.client import TelegramClient
from app.integrations.telegram.exceptions import TelegramError
from app.integrations.telegram.formatter import announcement
from app.integrations.telegram.service import TelegramSyncService
from app.repositories.admin import AdminRepository


@pytest.mark.parametrize(
    "description,code,flag",
    [
        ("Bad Request: message is not modified", 400, "not_modified"),
        ("Bad Request: message to edit not found", 400, "missing"),
        ("Unauthorized", 401, None),
        ("Forbidden", 403, None),
        ("Too Many Requests", 429, None),
        ("Internal Server Error", 500, "uncertain"),
    ],
)
async def test_telegram_transport_errors(monkeypatch, description, code, flag):
    monkeypatch.setattr(get_settings(), "telegram_bot_token", "never-expose-this-secret")

    async def handler(request):
        return httpx.Response(
            code, json={"ok": False, "error_code": code, "description": description}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(transport, "_http", http)
        with pytest.raises(TelegramError) as caught:
            await TelegramClient().call(
                "editMessageText", {"chat_id": 1, "message_id": 123, "text": "text"}
            )
        assert "never-expose" not in caught.value.message
        if flag:
            assert getattr(caught.value, flag)


async def test_timeout_is_ambiguous(monkeypatch):
    monkeypatch.setattr(get_settings(), "telegram_bot_token", "secret")

    async def handler(request):
        raise httpx.ReadTimeout("private-url-with-secret", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(transport, "_http", http)
        with pytest.raises(TelegramError) as caught:
            await TelegramClient().call("sendMessage", {})
        assert caught.value.uncertain
        assert "private-url" not in caught.value.message


async def test_concurrent_sync_uses_one_send(monkeypatch):
    url = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_test"
    )
    assert (make_url(url).database or "").endswith("_test")
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = get_settings()
    monkeypatch.setattr(settings, "telegram_bot_token", "test-only")
    monkeypatch.setattr(settings, "telegram_channel_id", "@channel")
    monkeypatch.setattr(settings, "site_url", "https://portfolio.example")
    post_id = uuid4()
    async with factory() as session:
        session.add(
            Post(
                id=post_id,
                title="Concurrent article",
                slug="concurrent-" + post_id.hex,
                content_html="<p>A useful article.</p>",
                status="published",
                published_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
    started, finish = asyncio.Event(), asyncio.Event()
    calls = []

    class SlowClient:
        async def call(self, method, payload):
            calls.append(method)
            started.set()
            await finish.wait()
            return {"message_id": 777, "chat": {"id": -100123}}

    try:
        async with factory() as first, factory() as second:
            job = asyncio.create_task(
                TelegramSyncService(AdminRepository(first), SlowClient()).sync(post_id)
            )
            await asyncio.wait_for(started.wait(), timeout=3)
            pending = await TelegramSyncService(AdminRepository(second), SlowClient()).sync(post_id)
            assert pending.telegram_sync_status == "pending"
            assert calls == ["sendMessage"]
            finish.set()
            result = await asyncio.wait_for(job, timeout=3)
            assert result.telegram_message_id == "777"
    finally:
        finish.set()
        async with factory() as session:
            await session.execute(delete(Post).where(Post.id == post_id))
            await session.commit()
        await engine.dispose()


def test_announcement_length_and_escaping(monkeypatch):
    monkeypatch.setattr(get_settings(), "site_url", "https://portfolio.example")
    post = Post(
        title="<b>" + "😀" * 200,
        slug="safe-slug",
        excerpt="😀 word & " * 1000,
        content_html="",
        tags=[],
    )
    text = announcement(post)

    class Text(HTMLParser):
        content = ""

        def handle_data(self, value):
            self.content += value

    parser = Text()
    parser.feed(text)
    assert len(parser.content.encode("utf-16-le")) // 2 < 1024
    assert "&lt;b&gt;" in text and "/writing/safe-slug" in text
