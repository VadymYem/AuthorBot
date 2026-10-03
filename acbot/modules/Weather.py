# ©️ AuthorChe
# 🌐 https://authorche.top
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3.

import logging
import re
from urllib.parse import quote_plus

import requests
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from herokutl.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineQuery
from ..utils import rand

__version__ = (1, 2, 0)

logger = logging.getLogger(__name__)
CYRILLIC = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")


def escape_ansi(line: str) -> str:
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


@loader.tds
class WeatherMod(loader.Module):
    """Weather forecast through wttr.in without blocking the event loop."""

    strings = {"name": "Weather"}

    async def _fetch(self, city: str, compact: bool = False) -> str:
        encoded = quote_plus(city.strip())
        language = "uk" if CYRILLIC.search(city) else "en"
        suffix = "?format=3" if compact else f"?m&T&lang={language}"
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
            "<b>🏙 Current city:</b> "
            f"<code>{utils.escape_html(city or 'Not specified')}</code>",
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
            await utils.answer(message, "<b>🏙 Specify a city or set one with .weathercity.</b>")
            return

        try:
            forecast = await self._fetch(city)
        except requests.RequestException as exc:
            logger.warning("Weather request failed", exc_info=True)
            await utils.answer(
                message,
                f"<b>Weather service error:</b> <code>{utils.escape_html(str(exc))}</code>",
            )
            return

        lines = "\n".join(forecast.splitlines()[:7])
        await utils.answer(message, f"<code>{utils.escape_html(lines)}</code>")

    async def weather_inline_handler(self, query: InlineQuery) -> None:
        """Переглянути прогноз погоди."""
        city = query.args.strip() or self.db.get(self.strings["name"], "city", "")
        if not city:
            return

        try:
            compact = await self._fetch(city, compact=True)
            full = await self._fetch(city)
            description = compact.strip()
            message_text = "\n".join(full.splitlines()[:7])
        except requests.RequestException:
            logger.warning("Inline weather request failed", exc_info=True)
            description = "Weather service is temporarily unavailable"
            message_text = description

        await query.answer(
            [
                InlineQueryResultArticle(
                    id=rand(20),
                    title=f"Forecast for {city}",
                    description=description,
                    input_message_content=InputTextMessageContent(
                        f"<code>{utils.escape_html(message_text)}</code>",
                        parse_mode="HTML",
                    ),
                )
            ],
            cache_time=30,
        )
