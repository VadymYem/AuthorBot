# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# ©️ Dan G. && AuthorChe
# 🌐 https://authorche.top
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3.

import hashlib
import logging
import re
import string

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message as AiogramMessage
from herokutl.errors.rpcerrorlist import YouBlockedUserError
from herokutl.tl.functions.contacts import UnblockRequest
from herokutl.tl.types import Message

from .. import loader, translations, utils
from ..public_pages import PAGES, rich_page, fallback_page, text as page_text
from ..branding import AUTHOR_PHOTO, BOT_PHOTO

logger = logging.getLogger(__name__)

PUBLIC_BOT_EDITORS = {6316376597, 6802848305}

START_RICH = rich_page("start", "ua")
HELP_RICH = rich_page("help", "ua")
ABOUT_RICH = rich_page("about", "ua")
AUTHOR_RICH = rich_page("author", "ua")
PROJECTS_RICH = rich_page("projects", "ua")
FALLBACK = {page: fallback_page(page, "ua") for page in PAGES}

# Recognize exact previously saved factory pages; keep editors' custom HTML.
LEGACY_DEFAULTS = {'start': ['795c39e88d1f3837292cd831dbb0b63888aa37437526368236c732287234296a', '301ff20507692d24e772e7c9d3964c95ea9ec7cce802ca4ae6f9a2ca0bd4dec9', '6a07b122f2f830aa4898534b3b004ff9481256c2ccfaa6e05bc6f88fa8614b3a', 'bc02712db77709e21f21f5ef8b85b88dbbc03ce88f4b0b719beee9d90f34fd14', 'f6e3de1b0d01c5c8605f015f77d615eef8f117f5c056fb59ccfc541bd79a6936', '388342e0cc44f97bdeadff407983be18cd9316fdf53adf5d85b3523e6570b4ef', '211119884e49597609ac958ef64d5037cb88358ab0c5088f915c03bad456dc58'], 'help': ['b1087188e17a8e08a9fa133d7b72cf565c8985662c4dda9c9268262de0fca120', 'aa0a8742372f45cb8a1e518d1593c8d892280569fec503b1963093e7ec38d8bb', 'a0383e8e69165688e8292bc81cd84be7b230c5ac1fbdd58f3aa10ec9f7003961', '1427ab14b69fb0bf9591ac82014419a7857cdedc05928cb6186d2360b78a01d8', 'f9da734695150aa35c1b0bc4cff73eeef84e971c6c6acc4bcdcb17047684b006', 'f27fcda0eb7c2b5fcf32f0b98979753573ad651fa8d2296ac14487bf5e0caf9b', '28fb57dc2714696bfae9c32b2861da6c02eb80dfc0f958646f338afb404c7090'], 'about': ['fce248080d03251a8ea6a9b353e01849bd658f6a6cad636f4397a9222d4cd7e4', '3c8d8853678acf7bf512a343d9b06b0a9977b5921b4b2199d1b673f2f494053f', 'b7f67e64ae64e7bdc655cbdd88e0eb08d03bc1641fd68de90fffa684802a9e78', 'b548ffd195a68c8940166ea588d4c99f5901e8d222bbaf2bb26e4ef3e400b6de', 'e38be06af2f3bb28dd3774fafe8c932893d0959a64fe4b292f698b79fd134772', 'f09a52616e80abd6a8eebe9279ea076194807a147ac713276065f0377a5caee6', 'ae76b0ac804f338ba39cc0a64af0b96b01587a84d54831a9a31e456f54a48f85'], 'projects': ['ed29ac332306fba0037e1f9a7ca2d50dd880ba6f47c7a15af3dc29d6af3a539d', 'f28afe004ddc0c40a65ea7ab0a9e1fa54424b79696a1c4c81a425e743313c255', '709054d5cc674a3848bc9f503f28604514f64c6483b0f7bbf70c594ac113c1db', '7b81ca670fb1efb52e4b2b36e715b07344e9f77e425725039821f8ff3d5bc84b', '60fb9cb07da224cb2bc22f7e1c58588287409493528e4d709706a105e594f316', '6f5913693e00a58851ef4e01b38e61d5df9ee79433045a00a0a17789a88d47d4', '1d97444a4418ac55547f83fd87dbb44709fcb07ff0da74baa3ac244f01ca6768'], 'author': ['2619daa25b1c308d3f09b33c94d4efd166850da3de34114d779b62df89ce52da', '405ec067509ee16db53d432597a08964fa8d601c65d36b823a56f8e6e0cde518', '46c91ad376a8027ffc59945877847f1e9331892166cfda9f1d39118410a3b2a6', 'afd9b604f37f433db937db9ebc21dfb9b7c0ffe0892c6fc1723a07006540a03a', 'cfa8039e3501536891087ac5cce15dff623ff957775693354e537c78fe28b866']}

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
        if requested and translations.normalize_language(requested) in translations.SUPPORTED_LANGUAGES:
            return translations.normalize_language(requested)
        visitor = getattr(getattr(message, "from_user", None), "language_code", None)
        if visitor:
            language = translations.normalize_language(visitor)
            return language if language in translations.SUPPORTED_LANGUAGES else "en"
        languages = self._db.get(translations.__name__, "lang", "ua").split()
        return next((translations.normalize_language(lang) for lang in languages
                     if translations.normalize_language(lang) in translations.SUPPORTED_LANGUAGES), "en")

    def _public_rich(self, page: str, language: str = "ua") -> str:
        if page == "help":
            # Public help is a fixed allowlist, never a saved owner command list.
            return rich_page(page, language)
        saved = self.get(f"public_{page}_rich", None)
        if saved and hashlib.sha256(saved.encode()).hexdigest() not in LEGACY_DEFAULTS.get(page, ()):
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

        if page == "help":
            self.set("public_help_rich", None)
            await message.answer("✅ Публічна довідка містить лише загальнодоступні команди й оновлюється автоматично.")
            return

        value = value.strip()
        if not value:
            await message.answer(
                f"Надішліть rich HTML після команди. Для скидання: <code>/set{page} reset</code>"
            )
            return

        if value.lower() == "reset":
            self.set(f"public_{page}_rich", None)
            await message.answer(f"✅ Сторінку <code>{page}</code> скинуто до стандартної.")
            return

        self.set(f"public_{page}_rich", value)
        await message.answer(
            f"✅ Rich Message для <code>/{page}</code> оновлено. Перевірка: <code>/{page}</code>"
        )

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
