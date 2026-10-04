# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# ©️ AuthorChe
# 🌐 https://authorche.top
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3.

import logging
import re
from urllib.parse import quote_plus

import requests
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from herokutl.tl.types import Message

from .. import loader, translations, utils
from ..inline.types import InlineQuery
from ..utils import rand

__version__ = (1, 2, 0)

logger = logging.getLogger(__name__)


def escape_ansi(line: str) -> str:
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


@loader.tds
class WeatherMod(loader.Module):
    """Weather forecast through wttr.in without blocking the event loop."""

    strings = {"name": "Weather"}

    async def _fetch(self, city: str, compact: bool = False) -> str:
        encoded = quote_plus(city.strip())
        selected = self._db.get(translations.__name__, "lang", "en").split()
        language = translations.normalize_language(selected[0]) if selected else "en"
        language = "uk" if language == "ua" else language
        if language not in {"uk", "en", "ru", "de", "ja"}:
            language = "en"
        suffix = f"?format=3&lang={language}" if compact else f"?m&T&lang={language}"
        response = await utils.run_sync(
            requests.get,
            f"https://wttr.in/{encoded}{suffix}",
            headers={"User-Agent": "AuthorBot/Weather"},
            timeout=12,
        )
        response.raise_for_status()
        return escape_ansi(response.text)

    @loader.command()
    async def weathercity(self, message: Message) -> None:
        """<city> — set the default forecast city."""
        if args := utils.get_args_raw(message):
            self.db.set(self.strings["name"], "city", args.strip())

        city = self.db.get(self.strings["name"], "city", "")
        await utils.answer(
            message,
            self.strings("city").format(utils.escape_html(city or self.strings("not_set"))),
        )

    @loader.command()
    async def weather(self, message: Message) -> None:
        """[city] — show the current forecast."""
        city = utils.get_args_raw(message).strip() or self.db.get(
            self.strings["name"],
            "city",
            "",
        )
        if not city:
            await utils.answer(message, self.strings("need_city").format(utils.escape_html(self.get_prefix())))
            return

        try:
            forecast = await self._fetch(city)
        except requests.RequestException as exc:
            logger.warning("Weather service unavailable (%s)", type(exc).__name__)
            await utils.answer(
                message,
                self.strings("unavailable"),
            )
            return

        lines = "\n".join(forecast.splitlines()[:16])
        await utils.answer(message, self.strings("forecast").format(utils.escape_html(city)) + f"\n<pre>{utils.escape_html(lines)}</pre>")

    async def weather_inline_handler(self, query: InlineQuery) -> None:
        """Переглянути прогноз погоди."""
        city = query.args.strip() or self.db.get(self.strings["name"], "city", "")
        if not city:
            return

        try:
            compact = await self._fetch(city, compact=True)
            full = await self._fetch(city)
            description = compact.strip()
            message_text = "\n".join(full.splitlines()[:16])
        except requests.RequestException:
            logger.debug("Inline weather service unavailable")
            description = self.strings("unavailable_plain")
            message_text = description

        await query.answer(
            [
                InlineQueryResultArticle(
                    id=rand(20),
                    title=self.strings("forecast_plain").format(city),
                    description=description,
                    input_message_content=InputTextMessageContent(
                        f"<code>{utils.escape_html(message_text)}</code>",
                        parse_mode="HTML",
                    ),
                )
            ],
            cache_time=30,
        )
