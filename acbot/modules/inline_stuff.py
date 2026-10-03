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

from .. import loader, utils

logger = logging.getLogger(__name__)

PUBLIC_BOT_EDITORS = {6316376597, 6802848305}

START_RICH = """<h1>AuthorBot</h1>
<figure><img src="https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/authorbot_banner.jpg"/><figcaption>AuthorBot · by Author C</figcaption></figure>
<blockquote>Модульний Telegram userbot від Author C — автоматизація, inline-інструменти, модулі, локальні налаштування та сучасний Telegram Bot API.</blockquote>

<h3>Що тут є</h3>
<ul>
<li><b>Модульна система</b> — встановлення та оновлення функцій без переписування ядра.</li>
<li><b>Inline UI</b> — кнопки, форми, списки, галереї та керування прямо в Telegram.</li>
<li><b>Rich Messages</b> — заголовки, таблиці, details-блоки, цитати, медіа та rich-кнопки.</li>
<li><b>Приватність</b> — API-ключі й сесії не публікуються та не виводяться в стартових повідомленнях.</li>
</ul>

<details><summary>Публічні команди</summary>
<code>/start</code> — головна сторінка
<code>/help</code> — довідка
<code>/about</code> — про автора
<code>/projects</code> — проєкти Author C
</details>

<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://github.com/VadymYem/AuthorBot">GitHub</tg-button>
<tg-button type="url" style="success" url="https://authorche.top/ubot.html">Встановити</tg-button>
</tg-button-row>
<tg-button-row align="center">
<tg-button type="url" url="https://t.me/wsinfo">Telegram</tg-button>
<tg-button type="url" url="https://authorche.top">authorche.top</tg-button>
</tg-button-row>

<footer>AuthorBot • by Author C</footer>"""

HELP_RICH = """<h1>AuthorBot • Help</h1>
<p>Цей бот є публічним інтерфейсом встановленого AuthorBot. Базові команди доступні всім.</p>

<table bordered striped compact>
<tr><th>Команда</th><th>Дія</th></tr>
<tr><td><code>/start</code></td><td>Головна сторінка</td></tr>
<tr><td><code>/help</code></td><td>Ця довідка</td></tr>
<tr><td><code>/about</code></td><td>Інформація про Author C</td></tr>
<tr><td><code>/projects</code></td><td>Проєкти та посилання</td></tr>
</table>

<blockquote expandable>Встановлені модулі можуть додавати власні публічні inline-команди. Їх доступність визначається самим модулем і політикою безпеки власника userbot.</blockquote>

<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://github.com/VadymYem/AuthorBot">Документація</tg-button>
<tg-button type="url" url="https://t.me/wsinfo">Оновлення</tg-button>
</tg-button-row>"""

ABOUT_RICH = """<h1>Author C</h1>
<figure><img src="https://authorche.top/poems/logo.jpg"/><figcaption>Author C — автор і розробник</figcaption></figure>

<p>Український розробник, автор цифрових проєктів, музикант, співак, композитор і поет. Основний напрям технічних проєктів — приватність, Telegram, Android, автоматизація та AI-інструменти.</p>

<details open><summary>Ресурси</summary>
<a href="https://authorche.top">authorche.top</a>
<a href="https://t.me/wsinfo">Telegram / wsinfo</a>
</details>

<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://authorche.top">Website</tg-button>
<tg-button type="url" url="https://t.me/wsinfo">Telegram</tg-button>
</tg-button-row>"""

PROJECTS_RICH = """<h1>Проєкти Author C</h1>
<blockquote>Добірка основних активних продуктів і експериментальних платформ.</blockquote>

<h2>AuthorGram</h2>
<p>Telegram-клієнт для Android із фокусом на приватність, розширені налаштування, мультимедіа та гнучке керування інтерфейсом.</p>
<tg-button-row>
<tg-button type="url" style="success" url="https://play.google.com/store/apps/details?id=toss.authorgram.apk">Google Play</tg-button>
<tg-button type="url" url="https://t.me/authorgram_apk">Telegram</tg-button>
</tg-button-row>

<h2>AuthorBot</h2>
<p>Модульний Telegram userbot: автоматизація, inline-форми, керування модулями, backup, security, Rich Messages і self-update.</p>
<tg-button-row>
<tg-button type="url" style="primary" url="https://github.com/VadymYem/AuthorBot">GitHub</tg-button>
<tg-button type="url" url="https://authorche.top/ubot.html">Сторінка</tg-button>
</tg-button-row>

<h2>Jarvis | AuthorAi</h2>
<p>Android AI-agent із локальними GGUF-моделями, voice/live режимом, інструментами, файлами, офлайн-базами знань та керуванням пристроєм.</p>

<h2>Goose | AuthorBrowser</h2>
<p>Android-браузер із розширеними медіа-можливостями, блокуванням реклами, фоновим відтворенням та інтеграціями.</p>

<h2>Author AI</h2>
<p>Серверна AI-платформа та набір інтеграцій для агентних сценаріїв, інструментів і автоматизацій.</p>

<details><summary>Більше про проєкти</summary>
Новини, релізи та експерименти публікуються на <a href="https://t.me/wsinfo">t.me/wsinfo</a> і <a href="https://authorche.top">authorche.top</a>.
</details>

<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://authorche.top">Усі ресурси</tg-button>
<tg-button type="url" url="https://t.me/wsinfo">Новини</tg-button>
</tg-button-row>"""

FALLBACK = {
    "start": (
        "<b>AuthorBot</b>\n\n"
        "Модульний Telegram userbot від Author C.\n\n"
        "<b>Команди:</b> /start · /help · /about · /projects\n\n"
        "GitHub: https://github.com/VadymYem/AuthorBot\n"
        "Web: https://authorche.top"
    ),
    "help": (
        "<b>AuthorBot • Help</b>\n\n"
        "/start — головна сторінка\n"
        "/help — довідка\n"
        "/about — про автора\n"
        "/projects — проєкти\n\n"
        "Встановлені модулі можуть додавати власні публічні команди."
    ),
    "about": (
        "<b>Author C</b>\n\n"
        "Український розробник, автор цифрових проєктів, музикант, співак, композитор і поет.\n\n"
        "https://authorche.top\nhttps://t.me/wsinfo"
    ),
    "projects": (
        "<b>Проєкти Author C</b>\n\n"
        "• AuthorGram — Telegram-клієнт для Android\n"
        "• AuthorBot — модульний Telegram userbot\n"
        "• Jarvis | AuthorAi — Android AI-agent\n"
        "• Goose | AuthorBrowser — Android-браузер\n"
        "• Author AI — AI-платформа та інтеграції\n\n"
        "https://authorche.top"
    ),
}


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

    def _public_rich(self, page: str) -> str:
        defaults = {
            "start": START_RICH,
            "help": HELP_RICH,
            "about": ABOUT_RICH,
            "projects": PROJECTS_RICH,
        }
        return self.get(f"public_{page}_rich", defaults[page]) or defaults[page]

    async def _send_public_page(self, message: AiogramMessage, page: str):
        try:
            await self.inline.rich.send(
                message.chat.id,
                html=self._public_rich(page),
            )
            return
        except Exception:
            logger.warning("Rich message failed for public page %s", page, exc_info=True)

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("GitHub", url="https://github.com/VadymYem/AuthorBot"),
            InlineKeyboardButton("Website", url="https://authorche.top"),
        )
        await message.answer(
            FALLBACK[page],
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    async def _set_public_page(self, message: AiogramMessage, page: str, value: str):
        if message.from_user.id not in PUBLIC_BOT_EDITORS:
            return

        value = value.strip()
        if not value:
            await message.answer(
                f"Надішліть rich HTML після команди. Для скидання: <code>/set{page} reset</code>"
            )
            return

        if value.lower() == "reset":
            self.set(f"public_{page}_rich", {
                "start": START_RICH,
                "help": HELP_RICH,
                "about": ABOUT_RICH,
                "projects": PROJECTS_RICH,
            }[page])
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
            await message.answer("✅ <b>AuthorBot inline interface is ready.</b>")
            return

        public_pages = {
            "/start": "start",
            "/help": "help",
            "/about": "about",
            "/aboutauthor": "about",
            "/projects": "projects",
        }
        if command in public_pages:
            await self._send_public_page(message, public_pages[command])
            return

        admin_pages = {
            "/setstart": "start",
            "/sethelp": "help",
            "/setabout": "about",
            "/setprojects": "projects",
        }
        if command in admin_pages:
            await self._set_public_page(message, admin_pages[command], args)
