"""Telegram Bot API rich-message support.

Kept separate from aiogram 2.x so AuthorBot can use new Bot API methods
without a disruptive framework migration.
"""

import json
import logging
import typing

import requests

from .. import utils

logger = logging.getLogger(__name__)


class RichMessageError(RuntimeError):
    """Raised when Telegram rejects a rich-message request."""


class RichBotAPI:
    def __init__(self, token: str):
        self._token = token

    @staticmethod
    def _jsonable(value: typing.Any) -> typing.Any:
        if value is None:
            return None
        if hasattr(value, "to_python"):
            return value.to_python()
        if hasattr(value, "to_json"):
            try:
                return json.loads(value.to_json())
            except Exception:
                pass
        return value

    def _request_sync(self, method: str, payload: dict) -> typing.Any:
        # Never log the URL: it contains the bot token.
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RichMessageError("Telegram Bot API request failed") from None

        if not response.ok or not data.get("ok"):
            description = str(data.get("description", "Telegram rejected the request"))
            raise RichMessageError(description[:500])

        return data.get("result")

    async def request(self, method: str, **payload) -> typing.Any:
        payload = {
            key: self._jsonable(value)
            for key, value in payload.items()
            if value is not None
        }
        return await utils.run_sync(self._request_sync, method, payload)

    async def send(
        self,
        chat_id: typing.Union[int, str],
        *,
        html: str = None,
        markdown: str = None,
        blocks: typing.Optional[list] = None,
        media: typing.Optional[list] = None,
        reply_markup: typing.Any = None,
        disable_notification: bool = False,
        protect_content: bool = False,
    ) -> typing.Any:
        rich_message = {
            key: value
            for key, value in {
                "html": html,
                "markdown": markdown,
                "blocks": blocks,
                "media": media,
            }.items()
            if value is not None
        }
        if len([key for key in ("html", "markdown", "blocks") if key in rich_message]) != 1:
            raise ValueError("Exactly one of html, markdown, or blocks must be supplied")

        return await self.request(
            "sendRichMessage",
            chat_id=chat_id,
            rich_message=rich_message,
            reply_markup=reply_markup,
            disable_notification=disable_notification,
            protect_content=protect_content,
        )

    async def draft(
        self,
        chat_id: int,
        draft_id: int,
        *,
        html: str = None,
        markdown: str = None,
        blocks: typing.Optional[list] = None,
        can_stop: bool = True,
        keep_on_stop: bool = True,
    ) -> bool:
        if not draft_id:
            raise ValueError("draft_id must be non-zero")

        rich_message = {
            key: value
            for key, value in {
                "html": html,
                "markdown": markdown,
                "blocks": blocks,
            }.items()
            if value is not None
        }
        if len(rich_message) != 1:
            raise ValueError("Exactly one of html, markdown, or blocks must be supplied")

        return bool(
            await self.request(
                "sendRichMessageDraft",
                chat_id=chat_id,
                draft_id=draft_id,
                rich_message=rich_message,
                can_stop=can_stop,
                keep_on_stop=keep_on_stop,
            )
        )
