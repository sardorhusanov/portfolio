import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import Post
from app.integrations.telegram.client import TelegramClient
from app.integrations.telegram.exceptions import TelegramError
from app.integrations.telegram.formatter import announcement, cover_url, public_base
from app.repositories.admin import AdminRepository

log = logging.getLogger(__name__)


class TelegramSyncService:
    def __init__(self, repository: AdminRepository, client: TelegramClient | None = None) -> None:
        self.repo = repository
        self.client = client or TelegramClient()

    async def after_save(self, post_id: UUID) -> Post:
        """A committed website save succeeds even when Telegram needs manual attention."""
        try:
            return await self.sync(post_id)
        except AppError as error:
            post = await self.repo.post(post_id, lock=True)
            if post is None:
                raise
            post.telegram_sync_status = "failed"
            post.telegram_error = error.message
            await self.repo.session.commit()
            return post

    async def sync(self, post_id: UUID, recreate: bool = False, followup: bool = True) -> Post:
        post = await self.repo.post(post_id, lock=True)
        if not post:
            raise AppError("Article not found.", 404)
        if post.status != "published":
            raise AppError("Publish the article on the website before synchronizing Telegram.", 409)
        now = datetime.now(timezone.utc)
        busy = (
            post.telegram_sync_status == "pending"
            and post.telegram_sync_started_at
            and post.telegram_sync_started_at > now - timedelta(seconds=60)
        )
        if busy:
            # Another request owns the persisted send intent. Never start a duplicate send.
            await self.repo.session.commit()
            return post
        if post.telegram_delivery_uncertain and not recreate:
            raise AppError(
                "Delivery is uncertain. Check the channel first. Use explicit recreation "
                "only after resolving any existing announcement.",
                409,
            )
        settings = get_settings()
        creating = recreate or not post.telegram_message_id
        if not creating and post.telegram_error and "no longer exists" in post.telegram_error:
            raise AppError("This Telegram message is missing. Use Recreate Telegram post.", 409)
        try:
            if not settings.telegram_bot_token or not settings.telegram_channel_id:
                raise TelegramError(
                    "Telegram is not configured. Website publication succeeded; configure "
                    "the integration and retry."
                )
            text = announcement(post)
            photo = cover_url(post) if creating else None
        except TelegramError as error:
            post.telegram_sync_status = "failed"
            post.telegram_error = error.message
            await self.repo.session.commit()
            return post
        channel = settings.telegram_channel_id if creating else post.telegram_channel_id
        if not channel:
            raise AppError(
                "The stored Telegram channel is missing. Review and recreate the announcement.", 409
            )
        message_id = post.telegram_message_id
        message_type = (
            ("photo" if photo else "text") if creating else post.telegram_message_type or "text"
        )
        revision = post.revision
        post.telegram_sync_status = "pending"
        post.telegram_sync_started_at = now
        post.telegram_error = None
        # Persist the send intent BEFORE the network call. A crash cannot trigger a blind resend.
        post.telegram_delivery_uncertain = creating
        await self.repo.session.commit()
        payload = {"chat_id": channel, "parse_mode": "HTML"}
        if creating:
            method = "sendPhoto" if photo else "sendMessage"
            payload.update({"photo": photo, "caption": text} if photo else {"text": text})
        else:
            method = "editMessageCaption" if message_type == "photo" else "editMessageText"
            payload.update(
                {
                    "message_id": int(message_id),
                    "caption" if message_type == "photo" else "text": text,
                }
            )
        result = None
        failure = None
        try:
            result = await self.client.call(method, payload)
        except TelegramError as error:
            if not error.not_modified or creating:
                failure = error
        post = await self.repo.post(post_id, lock=True)
        if failure:
            post.telegram_sync_status = "failed"
            post.telegram_error = failure.message
            post.telegram_delivery_uncertain = bool(creating and failure.uncertain)
            log.warning(
                "telegram_sync_failed", extra={"post_id": str(post_id), "operation": method}
            )
        else:
            if creating:
                if not isinstance(result, dict) or not result.get("message_id"):
                    # An unexpected response is also ambiguous; preserve the no-resend guard.
                    post.telegram_sync_status = "failed"
                    post.telegram_error = (
                        "Telegram did not return a message ID. Check the channel before recreating."
                    )
                    await self.repo.session.commit()
                    return post
                post.telegram_message_id = str(result["message_id"])
                post.telegram_channel_id = str(result.get("chat", {}).get("id", channel))
                post.telegram_message_type = message_type
            post.telegram_sync_status = "synced" if post.revision == revision else "not_synced"
            post.telegram_error = None
            post.telegram_delivery_uncertain = False
            post.telegram_synced_at = datetime.now(timezone.utc)
            log.info("telegram_sync_success", extra={"post_id": str(post_id), "operation": method})
        await self.repo.session.commit()
        # If content changed while Telegram was responding, safely update the now-known ID.
        if followup and post.telegram_sync_status == "not_synced" and post.status == "published":
            return await self.sync(post_id, followup=False)
        return post

    async def delete_message(self, post_id: UUID) -> Post:
        post = await self.repo.post(post_id, lock=True)
        if not post:
            raise AppError("Article not found.", 404)
        if post.telegram_sync_status == "pending" or post.telegram_delivery_uncertain:
            raise AppError("Resolve the current Telegram operation first.", 409)
        if not post.telegram_message_id:
            return post
        channel, message_id = post.telegram_channel_id, int(post.telegram_message_id)
        post.telegram_sync_status = "pending"
        post.telegram_sync_started_at = datetime.now(timezone.utc)
        await self.repo.session.commit()
        try:
            await self.client.call("deleteMessage", {"chat_id": channel, "message_id": message_id})
        except TelegramError as error:
            if not error.missing:
                post = await self.repo.post(post_id, lock=True)
                post.telegram_sync_status = "failed"
                post.telegram_error = error.message
                await self.repo.session.commit()
                return post
        post = await self.repo.post(post_id, lock=True)
        post.telegram_message_id = None
        post.telegram_channel_id = None
        post.telegram_message_type = None
        post.telegram_sync_status = "not_synced"
        post.telegram_error = None
        await self.repo.session.commit()
        return post

    async def test_connection(self) -> dict:
        try:
            public_base()
            channel = get_settings().telegram_channel_id
            if not channel:
                raise TelegramError("Configure TELEGRAM_CHANNEL_ID first.")
            bot = await self.client.call("getMe", {})
            chat = await self.client.call("getChat", {"chat_id": channel})
            member = await self.client.call(
                "getChatMember", {"chat_id": channel, "user_id": bot["id"]}
            )
            if chat.get("type") != "channel":
                raise TelegramError("The configured destination must be a Telegram channel.")
            if member.get("status") != "creator" and not (
                member.get("status") == "administrator"
                and member.get("can_post_messages")
                and member.get("can_edit_messages")
            ):
                raise TelegramError(
                    "Give the bot channel administrator permission to post and edit messages."
                )
            return {
                "connected": True,
                "message": "Telegram connected",
                "bot": bot.get("username"),
                "channel": chat.get("title"),
            }
        except TelegramError as error:
            return {"connected": False, "message": error.message, "bot": None, "channel": None}
