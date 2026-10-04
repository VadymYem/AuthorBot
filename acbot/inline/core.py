# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

"""Inline buttons, galleries and other Telegram-Bot-API stuff"""

import asyncio
import contextlib
import hashlib
import logging
import time
import typing

from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, Unauthorized
from herokutl.errors.rpcerrorlist import InputUserDeactivatedError, YouBlockedUserError
from herokutl.tl.functions.contacts import UnblockRequest
from herokutl.tl.types import Message
from herokutl.utils import get_display_name

from .. import utils
from ..branding import BOT_PHOTO, bot_photo, personal_bot_name
from ..database import Database
from ..tl_cache import CustomTelegramClient
from ..translations import Translator
from ..public_pages import PUBLIC_LANGUAGES, bot_commands
from .bot_pm import BotPM
from .events import Events
from .form import Form
from .gallery import Gallery
from .list import List
from .query_gallery import QueryGallery
from .rich import RichBotAPI
from .token_obtainment import TokenObtainment
from .utils import Utils

logger = logging.getLogger(__name__)


class InlineManager(
    Utils,
    Events,
    TokenObtainment,
    Form,
    Gallery,
    QueryGallery,
    List,
    BotPM,
):
    """
    Inline buttons, galleries and other Telegram-Bot-API stuff
    :param client: Telegram client
    :param db: Database instance
    :param allmodules: All modules
    :type client: acbot.tl_cache.CustomTelegramClient
    :type db: acbot.database.Database
    :type allmodules: acbot.loader.Modules
    """

    def __init__(
        self,
        client: CustomTelegramClient,
        db: Database,
        allmodules: "Modules",  # type: ignore  # noqa: F821
    ):
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules
        self.translator: Translator = allmodules.translator

        self._units: typing.Dict[str, dict] = {}
        self._custom_map: typing.Dict[str, callable] = {}
        self.fsm: typing.Dict[str, str] = {}
        self._web_auth_tokens: typing.List[str] = []
        self._error_events: typing.Dict[str, asyncio.Event] = {}

        self._markup_ttl = 60 * 60 * 24
        self.init_complete = False

        self._token = db.get("acbot.inline", "bot_token", False)

        self._me: int = None
        self._name: str = None
        self._dp: Dispatcher = None
        self._task: asyncio.Future = None
        self._cleaner_task: asyncio.Future = None
        self.bot: Bot = None
        self.rich: RichBotAPI = None
        self.bot_id: int = None
        self.bot_username: str = None
        self._brand_photo_lock = asyncio.Lock()

    async def brand_photo(self) -> str:
        """Upload bundled artwork once per bot and artwork revision."""
        fingerprint = hashlib.sha256(BOT_PHOTO.read_bytes()).hexdigest()
        cache_key = f"{self.bot_id}:{fingerprint}"
        async with self._brand_photo_lock:
            cached = self._db.get("acbot.inline", "brand_photo", {})
            if cached.get("key") == cache_key and cached.get("file_id"):
                return cached["file_id"]
            sent = await self.bot.send_photo(self._me, photo=bot_photo(), disable_notification=True)
            file_id = sent.photo[-1].file_id
            self._db.set("acbot.inline", "brand_photo", {"key": cache_key, "file_id": file_id})
            with contextlib.suppress(Exception):
                await self.bot.delete_message(sent.chat.id, sent.message_id)
            return file_id

    async def _cleaner(self):
        """Cleans outdated inline units"""
        while True:
            for unit_id, unit in self._units.copy().items():
                if (unit.get("ttl") or (time.time() + self._markup_ttl)) < time.time():
                    await self._unload_unit(unit_id)

            await asyncio.sleep(5)

    async def _set_public_commands(self):
        await self.rich.request(
            "setMyCommands",
            commands=bot_commands(),
        )
        for language in PUBLIC_LANGUAGES:
            await self.rich.request(
                "setMyCommands", commands=bot_commands(language),
                language_code="uk" if language == "ua" else language,
            )
        # Clear the previously registered Japanese catalog so those clients
        # inherit the default English public commands after updating.
        await self.rich.request("deleteMyCommands", language_code="ja")

    async def register_manager(
        self,
        after_break: bool = False,
        ignore_token_checks: bool = False,
    ):
        """
        Register manager
        :param after_break: Loop marker
        :param ignore_token_checks: If `True`, will not check for token
        :type after_break: bool
        :type ignore_token_checks: bool
        :return: None
        :rtype: None
        """
        self._me = self._client.tg_id
        self._name = get_display_name(self._client.acbot_me)

        if not ignore_token_checks:
            is_token_asserted = await self._assert_token()
            if not is_token_asserted:
                self.init_complete = False
                return

        self.init_complete = True

        self.bot = Bot(token=self._token, parse_mode=ParseMode.HTML)
        self.rich = RichBotAPI(self._token)
        Bot.set_current(self.bot)
        self._bot = self.bot
        self._dp = Dispatcher(self.bot)

        try:
            bot_me = await self.bot.get_me()
            self.bot_username = bot_me.username
            self.bot_id = bot_me.id
        except Unauthorized:
            logger.critical("Token expired, revoking...")
            return await self._dp_revoke_token(False)

        # Configure the public-facing companion bot through the current Bot API.
        # Failure here must never prevent the userbot itself from starting.
        try:
            await self.rich.request("setMyName", name=personal_bot_name(self._name))
        except Exception as exc:
            logger.warning("Unable to update personal bot name (%s)", type(exc).__name__)
        try:
            await self._set_public_commands()
            await self.rich.request(
                "setMyDescription",
                description=(
                    "AuthorBot companion interface — modules, automation, inline tools "
                    "and Telegram Rich Messages by AuthorChe."
                ),
            )
            await self.rich.request(
                "setMyShortDescription",
                short_description="AuthorBot • modular Telegram userbot by AuthorChe",
            )
        except Exception:
            logger.warning("Unable to update public bot profile", exc_info=True)

        try:
            m = await self._client.send_message(self.bot_username, "/start acbot init")
        except (InputUserDeactivatedError, ValueError):
            self._db.set("acbot.inline", "bot_token", None)
            self._token = False

            if not after_break:
                return await self.register_manager(True)

            self.init_complete = False
            return False
        except YouBlockedUserError:
            await self._client(UnblockRequest(id=self.bot_username))
            try:
                m = await self._client.send_message(
                    self.bot_username, "/start acbot init"
                )
            except Exception:
                logger.critical("Can't unblock users bot", exc_info=True)
                return False
        except Exception:
            self.init_complete = False
            logger.critical("Initialization of inline manager failed!", exc_info=True)
            return False

        await self._client.delete_messages(self.bot_username, m)

        self._dp.register_inline_handler(
            self._inline_handler,
            lambda _: True,
        )

        self._dp.register_callback_query_handler(
            self._callback_query_handler,
            lambda _: True,
        )

        self._dp.register_chosen_inline_handler(
            self._chosen_inline_handler,
            lambda _: True,
        )

        self._dp.register_message_handler(
            self._message_handler,
            lambda *_: True,
            content_types=["any"],
        )

        old = self.bot.get_updates
        revoke = self._dp_revoke_token

        async def new(*args, **kwargs):
            nonlocal revoke, old
            try:
                return await old(*args, **kwargs)
            except TerminatedByOtherGetUpdates:
                await revoke()
            except Unauthorized:
                logger.critical("Got Unauthorized")
                await self._stop()

        self.bot.get_updates = new

        self._task = asyncio.ensure_future(self._dp.start_polling())
        self._cleaner_task = asyncio.ensure_future(self._cleaner())

    async def _stop(self):
        """Stop the bot"""
        self._task.cancel()
        self._dp.stop_polling()
        self._cleaner_task.cancel()

    def pop_web_auth_token(self, token: str) -> bool:
        """
        Check if web confirmation button was pressed
        :param token: Token to check
        :type token: str
        :return: `True` if token was found, `False` otherwise
        :rtype: bool
        """
        if token not in self._web_auth_tokens:
            return False

        self._web_auth_tokens.remove(token)
        return True

    async def _invoke_unit(self, unit_id: str, message: Message) -> Message:
        unit = self._units.get(unit_id)
        if unit is not None:
            unit["sent_event"] = asyncio.Event()
        event = asyncio.Event()
        self._error_events[unit_id] = event

        q: "InlineResults" = None  # type: ignore  # noqa: F821
        exception: Exception = None

        async def result_getter():
            nonlocal unit_id, q
            with contextlib.suppress(Exception):
                q = await self._client.inline_query(self.bot_username, unit_id)

        async def event_poller():
            nonlocal exception
            await asyncio.wait_for(event.wait(), timeout=10)
            if self._error_events.get(unit_id):
                exception = self._error_events[unit_id]

        result_getter_task = asyncio.ensure_future(result_getter())
        event_poller_task = asyncio.ensure_future(event_poller())

        _, pending = await asyncio.wait(
            [result_getter_task, event_poller_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

        self._error_events.pop(unit_id, None)

        if exception:
            raise exception  # skipcq: PYL-E0702

        if not q:
            raise Exception("No query results")

        sent = await q[0].click(
            message.chat_id if isinstance(message, Message) else message,
            reply_to=(
                message.reply_to_msg_id if isinstance(message, Message) else None
            ),
        )
        if sent is None or getattr(sent, "chat_id", None) is None or not getattr(sent, "id", None):
            raise RuntimeError("Telegram sent an inline result without a recoverable message ID")
        if unit is not None:
            unit.update(chat=sent.chat_id, message_id=sent.id)
            unit["sent_event"].set()
        # Delete the accepted command even if Close races with the send reply.
        # Use this account directly: Message.delete is a no-op without _client.
        if isinstance(message, Message) and message.out:
            try:
                await self._client.delete_messages(message.chat_id, [message.id])
            except Exception as exc:
                logger.warning("Unable to delete accepted inline command (%s)", type(exc).__name__)
        return sent
