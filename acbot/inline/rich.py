# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

"""Telegram Bot API rich-message support.

Kept separate from aiogram 2.x so AuthorBot can use new Bot API methods
without a disruptive framework migration.
"""

import json
import contextlib
import logging
import re
import typing
from pathlib import Path

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
        if isinstance(value, dict):
            return {key: RichBotAPI._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [RichBotAPI._jsonable(item) for item in value]
        if hasattr(value, "to_python"):
            return RichBotAPI._jsonable(value.to_python())
        if hasattr(value, "to_json"):
            try:
                return json.loads(value.to_json())
            except Exception:
                pass
        return value

    def _request_sync(self, method: str, payload: dict, files: dict = None, timeout=30) -> typing.Any:
        # Never log the URL: it contains the bot token.
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        try:
            with contextlib.ExitStack() as stack:
                if files:
                    uploads = {
                        key: (Path(path).name, stack.enter_context(Path(path).open("rb")))
                        for key, path in files.items()
                    }
                    data = {key: json.dumps(value, ensure_ascii=False) for key, value in payload.items()}
                    # Plain strings must not gain JSON quotation marks in form fields.
                    data.update({key: value for key, value in payload.items() if isinstance(value, str)})
                    response = requests.post(url, data=data, files=uploads, timeout=timeout)
                else:
                    response = requests.post(url, json=payload, timeout=timeout)
            data = response.json()
        except (requests.RequestException, ValueError, OSError):
            raise RichMessageError("Telegram Bot API request failed") from None

        if not isinstance(data, dict):
            raise RichMessageError("Telegram Bot API returned an invalid response")
        if not response.ok or not data.get("ok"):
            description = str(data.get("description", "Telegram rejected the request"))
            raise RichMessageError(description.replace(self._token, "[redacted]")[:500])

        return data.get("result")

    async def request(self, method: str, *, _files: dict = None, _timeout=30, **payload) -> typing.Any:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", method):
            raise ValueError("Invalid Bot API method name")
        payload = {
            key: self._jsonable(value)
            for key, value in payload.items()
            if value is not None
        }
        return await utils.run_sync(self._request_sync, method, payload, _files, _timeout)

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
        files: typing.Optional[dict] = None,
        timeout=30,
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
            _files=files,
            _timeout=timeout,
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
