import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.telegram.exceptions import TelegramError

# httpx info logs include request URLs, and Telegram embeds the secret in the URL.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
_http: httpx.AsyncClient | None = None


async def close_client() -> None:
    global _http
    if _http:
        await _http.aclose()
        _http = None


class TelegramClient:
    async def call(self, method: str, payload: dict[str, Any]) -> dict[str, Any] | bool:
        global _http
        token = get_settings().telegram_bot_token
        if not token:
            raise TelegramError("Telegram is not configured. Set the bot token and channel first.")
        if _http is None:
            _http = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0), follow_redirects=False
            )
        try:
            response = await _http.post(
                f"https://api.telegram.org/bot{token}/{method}", json=payload
            )
            if response.status_code >= 500:
                raise TelegramError(
                    "Telegram is temporarily unavailable. Check the channel before retrying "
                    "a new announcement.",
                    uncertain=True,
                )
            result = response.json()
        except httpx.ConnectError:
            raise TelegramError("Could not connect to Telegram. Try again later.") from None
        except (httpx.HTTPError, ValueError):
            raise TelegramError(
                "Telegram did not confirm delivery. Check the channel before trying "
                "another announcement.",
                uncertain=True,
            ) from None
        if not isinstance(result, dict) or (result.get("ok") and "result" not in result):
            raise TelegramError(
                "Telegram returned an unexpected response. Check the channel before recreating.",
                uncertain=True,
            )
        if not result.get("ok"):
            description = str(result.get("description", "")).lower()
            code = result.get("error_code", response.status_code)
            if "message is not modified" in description:
                raise TelegramError("Already up to date.", not_modified=True)
            if (
                "message to edit not found" in description
                or "message to delete not found" in description
            ):
                raise TelegramError(
                    "The Telegram message no longer exists. Recreate it explicitly if needed.",
                    missing=True,
                )
            if code == 429:
                raise TelegramError("Telegram rate limit reached. Wait before retrying.")
            if code == 401:
                raise TelegramError(
                    "Telegram rejected the bot credentials. Check server configuration."
                )
            if code == 403 or "not enough rights" in description:
                raise TelegramError(
                    "The bot needs permission to post and edit messages in this channel."
                )
            if "chat not found" in description:
                raise TelegramError(
                    "The channel is unavailable. Check the channel ID and bot membership."
                )
            if "photo" in description or "image" in description or "url" in description:
                raise TelegramError(
                    "Telegram could not read the cover image. Check its public URL or remove "
                    "the cover and retry."
                )
            raise TelegramError(
                "Telegram rejected this request. Check the channel configuration and "
                "message permissions."
            )
        return result["result"]
