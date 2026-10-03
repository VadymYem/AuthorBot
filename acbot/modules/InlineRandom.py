# © Dan G. && AuthorChe
#
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
#  https://www.gnu.org/licenses/agpl-3.0.html
# -*- coding: utf-8 -*-

from random import choice, randint
import asyncio
import re

import aiohttp

from .. import loader, utils
from ..inline.types import InlineQuery


@loader.tds
class InlineRandomMod(loader.Module):
    """Random tools for your userbot"""

    strings = {"name": "InlineRandom"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "person_photo_url", "", lambda: self.strings("person_source_doc"),
                validator=loader.validators.String(),
            ),
        )

    @loader.inline_everyone
    async def coin_inline_handler(self, query: InlineQuery) -> dict:
        """Heads or tails?"""

        r = self.strings("heads") if randint(0, 1) else self.strings("tails")

        return {
            "title": self.strings("coin_title"),
            "description": "AuthorBot · by AuthorChe",
            "message": f"<b>🪙 {self.strings('coin_title')}</b>\n\n{r}",
            "thumb": "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
        }

    @loader.inline_everyone
    async def random_inline_handler(self, query: InlineQuery) -> dict:
        """[number] - Send random number less than specified"""

        if not query.args:
            return

        a = query.args

        if not re.fullmatch(r"[0-9]{1,12}", a) or int(a) < 1:
            return

        return {
            "title": self.strings("number_title").format(a),
            "description": "AuthorBot · by AuthorChe",
            "message": f"<b>🎲 {self.strings('number_title').format(a)}</b>\n\n<code>{randint(1, int(a))}</code>",
            "thumb": "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
        }

    @loader.inline_everyone
    async def choice_inline_handler(self, query: InlineQuery) -> dict:
        """[args, separated by comma] - Make a choice"""

        if not query.args or not query.args.count(","):
            return

        items = [item.strip() for item in query.args.split(',') if item.strip()]
        if len(items) < 2:
            return

        return {
            "title": self.strings("choice_title"),
            "description": "AuthorBot · by AuthorChe",
            "message": (
                f"<b>✦ {self.strings('choice_title')}</b>\n\n"
                f"<b>{utils.escape_html(choice(items))}</b>"
            ),
            "thumb": "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
        }

    @loader.inline_everyone
    async def person_inline_handler(self, query: InlineQuery) -> dict:
        """Send a portrait from the configured image service."""
        url = self.config["person_photo_url"].replace("{seed}", utils.rand(10))
        if not url:
            return {"title": self.strings("person_title"), "message": self.strings("person_setup")}
        if not url.startswith(("https://", "http://")) or not utils.check_url(url):
            return {"title": self.strings("person_title"), "message": self.strings("person_unavailable")}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    # Inline photos must be actual JPEG/PNG images, not HTML
                    # pages, redirects to a parked domain or a retired API.
                    header = await response.content.readexactly(8)
                    if not header.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")):
                        raise ValueError("not an image")
        except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.IncompleteReadError, ValueError):
            return {"title": self.strings("person_title"), "message": self.strings("person_unavailable")}
        return {"photo": url, "title": self.strings("person_title")}
