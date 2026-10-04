# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# © Dan G. && AuthorChe
#
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
#  https://www.gnu.org/licenses/agpl-3.0.html
# -*- coding: utf-8 -*-

import herokutl
from herokutl.extensions.html import CUSTOM_EMOJIS
from herokutl.tl.types import Message

from .. import loader, main, utils, version
from ..branding import BOT_PHOTO
from ..inline.types import InlineCall
import random


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {"name": "Settings",
               "acbt": '''
    ✌️ <b>Привіт!</b>
    
    <b>Юзербот</b> — це бот, який працює від імені звичайного користувача Telegram, надаючи розширені можливості, недоступні для класичних ботів. Наприклад, юзербот може читати повідомлення після їх надсилання, шукати інфо в гугл та виконувати інші дії, як і звичайний бот, але від імені користувача.
    
    <b>AuthorBot</b> — це один із найсучасніших юзерботів, який відрізняється високою продуктивністю та унікальними функціями. Ось його основні переваги:
    
    - 🆕 <b>Останні оновлення Telegram</b>: підтримка реакцій, відео-наклейок, цитат та інших нових функцій.
    - 🔓 <b>Поліпшена безпека</b>: вбудоване кешування сутностей та цільові правила безпеки.
    - 🎨 <b>Покращений інтерфейс</b>: зручний дизайн та оптимізована взаємодія з користувачем.
    - 📼 <b>Нові модулі</b>: оновлені та додані нові основні модулі для розширення функціоналу.
    - ⏱ <b>Стабільність та швидкість</b>: швидка робота та мінімальні затримки.
    - ▶️ <b>Вбудовані форми, галереї та списки</b>: зручні інструменти для взаємодії з користувачем.
    - 👨‍👦 <b>Підтримка NoNick</b>: можливість використовувати інший акаунт для роботи юзербота.
    - 🔁 <b>Повна сумісність</b>: працює з популярними юзерботами на базі Telethon.
    - 🇺🇦 <b>Підтримка української мови</b>: унікальна функція, яка відрізняє AuthorBot від інших.
    - <b>Унікальні модулі</b>: розроблені спеціально автором для покращення функціоналу.
    
    AuthorBot — це ідеальний вибір для тих, хто шукає сучасний, безпечний та зручний інструмент для автоматизації в Telegram.
    
    <b>🌍 </b><a href="https://authorche.top/">WebSite</a>
    <b>👥 </b><a href="http://www.instagram.com/Vadym_Yem">Instagram😎</a>
    '''}

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid
    
    @loader.command()
    async def authorcmd(self, message: Message):
        await utils.answer(message, self.strings("acbt"))
            
    @loader.command()
    async def blacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    @loader.command()
    async def unblacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(set(self._db.get(main.__name__, "blacklist_chats", [])) - {chatid}),
        )

        await utils.answer(message, self.strings("unblacklisted").format(chatid))

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            if reply := await message.get_reply_message():
                return reply.sender_id

            return message.to_id.user_id if message.is_private else False

    @loader.command()
    async def blacklistuser(self, message: Message):
        if not (user := await self.getuser(message)):
            await utils.answer(message, self.strings("who_to_blacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    @loader.command()
    async def unblacklistuser(self, message: Message):
        if not (user := await self.getuser(message)):
            await utils.answer(message, self.strings("who_to_unblacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - {user}),
        )

        await utils.answer(
            message,
            self.strings("user_unblacklisted").format(user),
        )

    @loader.command()
    async def setprefix(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        if args == "s":
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = utils.escape_html(self.get_prefix())

        self._db.set(
            main.__name__,
            "command_prefix",
            args,
        )
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                "<emoji document_id=5197474765387864959>👍</emoji>",
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.command()
    async def aliases(self, message: Message):
        await utils.answer(
            message,
            self.strings("aliases")
            + "\n".join(
                [
                    f"<emoji document_id=4974259868996207180>🛑</emoji> <code>{i}</code> &lt;- {y}"
                    for i, y in self.allmodules.aliases.items()
                ]
            ),
        )

    @loader.command()
    async def addalias(self, message: Message):
        if len(args := utils.get_args(message)) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        if self.allmodules.add_alias(alias, cmd):
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.command()
    async def delalias(self, message: Message):
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]

        if not self.allmodules.remove_alias(alias):
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )
            return

        current = self.get("aliases", {})
        del current[alias]
        self.set("aliases", current)
        await utils.answer(
            message,
            self.strings("alias_removed").format(utils.escape_html(alias)),
        )

    @loader.command()
    async def cleardb(self, message: Message):
        await self.inline.form(
            self.strings("confirm_cleardb"),
            message,
            reply_markup=[
                {
                    "text": self.strings("cleardb_confirm"),
                    "callback": self._inline__cleardb,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    async def _inline__cleardb(self, call: InlineCall):
        self._db.clear()
        self._db.save()
        await utils.answer(call, self.strings("db_cleared"))

    async def installationcmd(self, message: Message):
        """| Guide of installation"""

        await self.client.send_file(
            message.peer_id,
            str(BOT_PHOTO),
            caption=self.strings["installation"].format('{}', prefix=self.get_prefix()), reply_to=getattr(message, "reply_to_msg_id", None),)
    
        await message.delete()
