
#              © Copyright 2022
#           https://t.me/authorche
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os

import telethon
from telethon.tl.types import Message
from telethon.extensions.html import CUSTOM_EMOJIS

from .. import loader, main, translations, utils, version
from ..inline.types import InlineCall


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Too many args</b>"
        ),
        "blacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Chat {} blacklisted'
            " from userbot</b>"
        ),
        "unblacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Chat {}'
            " unblacklisted from userbot</b>"
        ),
        "user_blacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>User {} blacklisted'
            " from userbot</b>"
        ),
        "user_unblacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>User {}'
            " unblacklisted from userbot</b>"
        ),
        "what_prefix": "❓ <b>What should the prefix be set to?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Prefix must be one"
            " symbol in length</b>"
        ),
        "prefix_set": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Command prefix'
            " updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to"
            " change it back</b>"
        ),
        "alias_created": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Alias created.'
            " Access it with</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliases:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Command</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You must provide a"
            " command and the alias for it</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You must provide the"
            " alias name</b>"
        ),
        "alias_removed": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Alias</b>'
            " <code>{}</code> <b>removed</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "db_cleared": (
            '<emoji document_id="5368324170671202286">👍</emoji><b> Database cleared</b>'
        ),
        "acbot": (
            "{}\n\n<emoji document_id=5388929052935462187>😎</emoji> <b>Version:"
            " {}.{}.{}</b>\n<emoji document_id=5228804314134226293>💪</emoji> <b>Build:"
            " </b><i>{}</i>\n\n <emoji document_id=5247224183326256799>👌</emoji>"
            " <b>Author-TL: </b><i>{}</i>\n\n"
            "<b>💻 Developer: \n"
            "t.me/AuthorChe or t.me/ac_ubot</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You need to specify"
            " valid url containing a langpack</b>"
        ),
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Translate pack'
            " saved!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Incorrect language"
            " specified</b>"
        ),
        "lang_removed": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Translations reset'
            " to default ones</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Invalid pack format"
            " in url</b>"
        ),
        "confirm_cleardb": "⚠️ <b>Are you sure, that you want to clear database?</b>",
        "cleardb_confirm": "🗑 Clear database",
        "cancel": "🚫 Cancel",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Who to blacklist?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Who to"
            " unblacklist?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>You are using an"
            " unstable branch </b><code>{}</code><b>!</b>"
        ),
    }

    strings_ua = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Надто багато"
            " аргументів</b>"
        ),
        "blacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Чат {} додано до'
            " чорного списку AuthorChe's</b>"
        ),
        "unblacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Чат {} видалено з'
            " чорного списку AuthorChe's</b>"
        ),
        "user_blacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Користувача {}'
            " додано до чорного списку AuthorChe's</b>"
        ),
        "user_unblacklisted": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Користувача {}'
            " видалено з чорного списку AuthorChe's</b>"
        ),
        "what_prefix": "❓ <b>А який префікс мені ставити?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Префікс має"
            " складатися тільки з одного символу</b>"
        ),
        "prefix_set": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Префікс змінено.'
            " Щоб повернути його, використовуй</b> <code>{newprefix}setprefix"
            " {oldprefix}</code>"
        ),
        "alias_created": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Аліас створено.'
            " Використовуй його через</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Аліаси:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Команди</b>"
            " <code>{}</code> <b>немає в моїй системі</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Потрібно ввести"
            " команду й аліас для неї</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Потрібне ім`я"
            " аліасу</b>"
        ),
        "alias_removed": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Аліас</b>'
            " <code>{}</code> <b>видалено</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b> Аліасу</b>"
            " <code>{}</code> <b>немає в моїй системі</b>"
        ),
        "db_cleared": (
            '<emoji document_id="5368324170671202286">👍</emoji><b> База очищена</b>'
        ),
        "acbot": (
            "{}\n\n<emoji document_id=5388929052935462187>😎</emoji> <b>Версія:"
            " {}.{}.{}</b>\n<emoji document_id=5228804314134226293>💪</emoji> <b>Build:"
            " </b><i>{}</i>\n\n<emoji document_id=5247224183326256799>👌</emoji> "
            " <b>Author's Bot: </b><i>{}</i>\n\n<emoji"
            "<b>💻 Розробник: \n"
            " t.me/AuthorChe або t.me/ac_ubot</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Вкажи правильне"
            " посилання, на пак с перекладом</b>"
        ),
        "lang_saved": "{} <b>Мову збережено!</b>",
        "pack_saved": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Пак перекладу'
            " збережено!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Вказано неправильну"
            " мову</b>"
        ),
        "lang_removed": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Переклади'
            " скинуті</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>За посиланням знаходиться"
            " неправильний пак</b>"
        ),
        "_cls_doc": "Керування базовими нплаштуваннями AuthorChe's",
        "confirm_cleardb": "⚠️ <b>Ви впевнені, що хочете скинути базу даних?</b>",
        "cleardb_confirm": "🗑 Очистити базу",
        "cancel": "🚫 Відміна",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Кого заблокувати"
            " ?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Кого розблокувати"
            " ?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Ти використовуєш"
            " нестабільну гілку </b><code>{}</code><b>!</b>"
        ),
    }

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

    @loader.command(ru_doc="Показать версию acbot")
    async def authorcmd(self, message: Message):
        """Get acbot version"""
        await utils.answer(
            message,
            self.strings("acbot").format(
                (
                    utils.get_platform_emoji()
                    + (
                        "✌ <b>AuthorChe's bot<\b>"

                        if "LAVHOST" in os.environ
                        else ""
                    )
                )
                if self._client.acbot_me.premium and CUSTOM_EMOJIS
                else "✌ <b>AuthorChe's bot</b>",
                *version.__version__,
                utils.get_commit_url(),
                f"{telethon.__version__} #{telethon.tl.alltlobjects.LAYER}",
            )
            + (
                ""
                if version.branch == "main"
                else self.strings("unstable").format(version.branch)
            ),
        )

    @loader.command(ua_doc="[чат] [модуль] - Вимнути бота будь де")
    async def blacklist(self, message: Message):
        """[chat_id] [module] - Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    @loader.command(ua_doc="[чат] - Ввімкнути бота будь де")
    async def unblacklist(self, message: Message):
        """<chat_id> - Unblacklist the bot from operating somewhere"""
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
            reply = await message.get_reply_message()

            if reply:
                return reply.sender_id

            return message.to_id.user_id if message.is_private else False

    @loader.command(ua_doc="[користувач] - Заборонити користувачу виконувати команди")
    async def blacklistuser(self, message: Message):
        """[user_id] - Prevent this user from running any commands"""
        user = await self.getuser(message)

        if not user:
            await utils.answer(message, self.strings("who_to_blacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    @loader.command(ua_doc="[користувач] - Дозволити користувачу виконувати команди")
    async def unblacklistuser(self, message: Message):
        """[user_id] - Allow this user to run permitted commands"""
        user = await self.getuser(message)

        if not user:
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

    @loader.owner
    @loader.command(ua_doc="<префікс> - Встановити префікс команд")
    async def setprefix(self, message: Message):
        """<prefix> - Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = self.get_prefix()
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    @loader.command(ua_doc="Показати список алиасів")
    async def aliases(self, message: Message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases")

        string += "\n".join(
            [f"▫️ <code>{i}</code> &lt;- {y}" for i, y in aliases.items()]
        )

        await utils.answer(message, string)

    @loader.owner
    @loader.command(ua_doc="Встановити аліас для команди")
    async def addalias(self, message: Message):
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
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

    @loader.owner
    @loader.command(ua_doc="Видалити аліас для команди")
    async def delalias(self, message: Message):
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]
        removed = self.allmodules.remove_alias(alias)

        if not removed:
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

    @loader.command(ua_doc="[посилання на пак] - Змінити зовнішній пак перекладу")
    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change acbot translate pack (external)
        """
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        success = await self.translator.init()
        await utils.answer(
            message, self.strings("pack_saved" if success else "check_pack")
        )

    @loader.command(ua_doc="[мови] - Змінити стандартну мову")
    async def setlang(self, message: Message):
        """[languages in the order of priority] - Change default language"""
        args = utils.get_args_raw(message)
        if not args or any(len(i) != 2 for i in args.split(" ")):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join(
                    [
                        utils.get_lang_flag(
                            lang.lower() if lang.lower() != "en" else "gb"
                        )
                        for lang in args.lower().split(" ")
                    ]
                )
            ),
        )

    @loader.owner
    @loader.command(ua_doc="Очистити базу даних")
    async def cleardb(self, message: Message):
        """Clear the entire database, effectively performing a factory reset"""
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
