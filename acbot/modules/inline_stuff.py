# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# ©️ Dan G. && AuthorChe
# 🌐 https://authorche.top
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3.

import logging
import re
import string

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message as AiogramMessage
from herokutl.errors.rpcerrorlist import YouBlockedUserError
from herokutl.tl.functions.contacts import UnblockRequest
from herokutl.tl.types import Message

from .. import loader, translations, utils
from ..public_pages import PAGES, public_language, rich_page, fallback_page, text as page_text
from ..branding import AUTHOR_PHOTO, BOT_PHOTO

logger = logging.getLogger(__name__)

PUBLIC_BOT_EDITORS = {6316376597, 6802848305}

START_RICH = rich_page("start", "ua")
HELP_RICH = rich_page("help", "ua")
ABOUT_RICH = rich_page("about", "ua")
AUTHOR_RICH = rich_page("author", "ua")
PROJECTS_RICH = rich_page("projects", "ua")
FALLBACK = {page: fallback_page(page, "ua") for page in PAGES}


@loader.tds
class InlineStuff(loader.Module):
    """Provides inline infrastructure and the public companion-bot interface."""

    strings = {"name": "InlineStuff"}

    @loader.watcher(
        "out",
        "only_inline",
        contains="This message will be deleted automatically",
    )
    async def watcher(self, message: Message):
        if message.via_bot_id == self.inline.bot_id:
            await message.delete()

    @loader.watcher("out", "only_inline", contains="Opening gallery...")
    async def gallery_watcher(self, message: Message):
        if message.via_bot_id != self.inline.bot_id:
            return

        match = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text or "")
        if not match:
            return

        unit_id = match[1]
        unit = self.inline._custom_map.get(unit_id)
        if not unit:
            return

        await message.delete()
        status = await message.respond("✍️", reply_to=utils.get_topic(message))
        await self.inline.gallery(
            message=status,
            next_handler=unit["handler"],
            caption=unit.get("caption", ""),
            force_me=unit.get("force_me", False),
            disable_security=unit.get("disable_security", False),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                request = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                request = await conv.send_message("/token")

            response = await conv.get_response()
            await request.delete()
            await response.delete()

            if not getattr(getattr(response, "reply_markup", None), "rows", None):
                return False

            for row in response.reply_markup.rows:
                for button in row.buttons:
                    if username == button.text.strip("@"):
                        cancel = await conv.send_message("/cancel")
                        cancelled = await conv.get_response()
                        await cancel.delete()
                        await cancelled.delete()
                        return True

        return False

    @loader.command()
    async def ch_acbot(self, message: Message):
        """<username> — use an existing BotFather bot as the AuthorBot inline bot."""
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(char not in (string.ascii_letters + string.digits + "_") for char in args)
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("acbot.inline", "custom_bot", args)
        self._db.set("acbot.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))

    def _language(self, message=None, requested=""):
        if message is not None:
            visitor = getattr(getattr(message, "from_user", None), "language_code", None)
            return public_language(visitor)
        languages = self._db.get(translations.__name__, "lang", "ua").split()
        return next((translations.normalize_language(lang) for lang in languages
                     if translations.normalize_language(lang) in translations.SUPPORTED_LANGUAGES), "en")

    def _public_rich(self, page: str, language: str = "ua") -> str:
        language = public_language(language)
        if page == "help":
            # Public help is a fixed allowlist, never a saved owner command list.
            return rich_page(page, language)
        # Unlabelled legacy HTML could override every visitor's translation.
        # New editor pages are stored independently for each public language.
        saved = self.get(f"public_{page}_rich_{language}", None)
        if saved and not re.search(r"Jarvis|AuthorAi|Goose|AuthorBrowser|Author AI", saved, re.I):
            return saved.replace("Author C", "AuthorChe")
        return rich_page(page, language, prefix=self.get_prefix())

    async def _send_public_page(self, message: AiogramMessage, page: str, requested: str = ""):
        language = self._language(message, requested)
        if page == "help":
            # Deliver the usable public catalog immediately, then upgrade that
            # same message to rich formatting. A slow/unsupported Rich API must
            # never make visitors wait without any response.
            sent = await message.answer(
                fallback_page("help", language), disable_web_page_preview=True,
            )
            try:
                await self.inline.rich.request(
                    "editMessageText", chat_id=message.chat.id, message_id=sent.message_id,
                    rich_message={"html": rich_page("help", language)}, _timeout=(3, 7),
                )
            except Exception:
                logger.debug("Rich public help unavailable; public catalog remains readable")
            return
        try:
            html = self._public_rich(page, language)
            # Migrate saved default pages without replacing editors' own content.
            for owner in ("VadymYem", "AuthorGramProject"):
                html = html.replace(
                    f"https://raw.githubusercontent.com/{owner}/AuthorBot/main/assets/bot_pfp.jpg",
                    "tg://photo?id=bot_artwork",
                )
            media = []
            files = {}
            for name, path in (("bot_artwork", BOT_PHOTO), ("author_artwork", AUTHOR_PHOTO)):
                if f"tg://photo?id={name}" in html:
                    media.append({"id": name, "media": {"type": "photo", "media": f"attach://{name}"}})
                    files[name] = path
            await self.inline.rich.send(
                message.chat.id,
                html=html,
                media=media or None,
                files=files or None,
                timeout=(3, 7),
            )
            return
        except Exception as exc:
            logger.warning("Rich page %s unavailable (%s); using classic message", page, type(exc).__name__)

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("GitHub", url="https://github.com/VadymYem/AuthorBot"),
            InlineKeyboardButton("authorche.top", url="https://authorche.top"),
        )
        await message.answer(
            fallback_page(page, language, prefix=self.get_prefix()),
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    async def _set_public_page(self, message: AiogramMessage, page: str, value: str):
        if message.from_user.id not in PUBLIC_BOT_EDITORS:
            return

        language = self._language(message)
        t = lambda key: page_text(key, language).format(page=page)
        if page == "help":
            self.set("public_help_rich", None)
            await message.answer(t("editor_help"))
            return

        value = value.strip()
        if not value:
            await message.answer(t("editor_usage"))
            return

        if value.lower() == "reset":
            self.set(f"public_{page}_rich_{language}", None)
            await message.answer(t("editor_reset"))
            return

        if re.search(r"Jarvis|AuthorAi|Goose|AuthorBrowser|Author AI", value, re.I):
            await message.answer(t("editor_private"))
            return
        self.set(f"public_{page}_rich_{language}", value)
        await message.answer(t("editor_saved"))

    async def aiogram_watcher(self, message: AiogramMessage):
        text = (message.text or "").strip()
        if not text.startswith("/"):
            return

        command, _, args = text.partition(" ")
        command = command.split("@", maxsplit=1)[0].lower()

        if command == "/start" and args.strip().lower() == "acbot init":
            await message.answer(page_text("ready", self._language(message)))
            return

        public_pages = {
            "/start": "start",
            "/help": "help",
            "/about": "about",
            "/author": "author",
            "/автор": "author",
            "/aboutauthor": "author",
            "/projects": "projects",
        }
        if command in public_pages:
            await self._send_public_page(message, public_pages[command], args.strip())
            return

        admin_pages = {
            "/setstart": "start",
            "/sethelp": "help",
            "/setabout": "about",
            "/setprojects": "projects",
            "/setauthor": "author",
        }
        if command in admin_pages:
            await self._set_public_page(message, admin_pages[command], args)

    @loader.command()
    async def author(self, message: Message):
        """— open the AuthorChe Rich Message page in your private inline-bot chat."""
        language = self._language()
        try:
            await self.inline.rich.send(
                self._client.tg_id, html=rich_page("author", language),
                media=[{"id": "author_artwork", "media": {"type": "photo", "media": "attach://author_artwork"}}],
                files={"author_artwork": AUTHOR_PHOTO},
            )
        except Exception:
            await self.inline.bot.send_message(self._client.tg_id, fallback_page("author", language), disable_web_page_preview=True)
        await utils.answer(message, page_text("sent_author", language))

    @loader.command()
    async def автор(self, message: Message):
        """— відкрити Rich Message сторінку AuthorChe у приватному чаті з inline-ботом."""
        await self.author(message)
