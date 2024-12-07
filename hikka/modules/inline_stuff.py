import re
import string
import abc
import time

from aiogram.types import Message as AiogramMessage
from telethon.utils import get_display_name
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .. import loader, utils
from ..inline.types import InlineCall

from hikkatl.errors.rpcerrorlist import YouBlockedUserError
from hikkatl.tl.functions.contacts import UnblockRequest
from hikkatl.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineMessage

@loader.tds
class InlineStuff(loader.Module):
    """Provides support for inline stuff"""

    strings = {"name": "InlineStuff",
        "start": (
            '✌️ <b>Привіт!\n'
            'Ви можете зв`язатися з Автором через </b>@vyfb_bot\n\n<i>Використай /menu для перегляду функціоналу</i>\n\n'
            '<b>🌍 </b><a href="https://authorche.pp.ua/"><b>WebSite</b></a>\n'
            '<b>👥 </b><a href="http://www.instagram.com/Vadym_Yem"><b>Instagram😎</b></a>'  
        ), 
    }

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

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text)[1]

        await message.delete()

        m = await message.respond("✍️", reply_to=utils.get_topic(message))

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    @loader.command()
    async def ch_acbot(self, message: Message):
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
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

        self._db.set("hikka.inline", "custom_bot", args)
        self._db.set("hikka.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))

    async def aiogram_watcher(self, message: AiogramMessage):
        if message.text == "/start":
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    text="Donate me💔",
                    url="https://authorche.pp.ua/donate.html"
                ),
                InlineKeyboardButton(
                    text="About Me😎✌️",
                    url="https://wsinfo.t.me/"
                )
            )
            await message.answer(
                self.strings("start"),
                reply_markup=keyboard
            )