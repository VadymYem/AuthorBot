
#              © Copyright 2022
#           https://t.me/authorche
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import atexit
import random
import sys
import os

import telethon
from telethon.tl.types import Message
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.utils import get_display_name

from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

ALL_INVOKES = [
    "clear_entity_cache",
    "clear_fulluser_cache",
    "clear_fullchannel_cache",
    "clear_perms_cache",
    "clear_cache",
    "reload_core",
    "inspect_cache",
    "inspect_modules",
]


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )


@loader.tds
class AcbotSettingsMod(loader.Module):
    """Advanced settings for acbot Userbot"""

    strings = {
        "name": "Settings",
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Watchers:</b>\n\n<b>{}</b>"
        ),
        "no_args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>No arguments"
            " specified</b>"
        ),
        "invoke404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Internal debug method"
            " </b><code>{}</code><b> not found, ergo can't be invoked</b>"
        ),
        "module404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Module</b>"
            " <code>{}</code> <b>not found</b>"
        ),
        "invoke": (
            "<emoji document_id=5215519585150706301>👍</emoji> <b>Invoked internal debug"
            " method </b><code>{}</code>\n\n<emoji"
            " document_id=5784891605601225888>🔵</emoji> <b>Result: \n{}</b>"
        ),
        "invoking": (
            "<emoji document_id=5213452215527677338>⏳</emoji> <b>Invoking internal"
            " debug method </b><code>{}</code><b> of </b><code>{}</code><b>...</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Watcher {} not"
            " found</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} is now"
            " <u>disabled</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} is now"
            " <u>enabled</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>You need to specify"
            " watcher name</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick for this user"
            " is now {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Please, specify"
            " command to toggle NoNick for</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick for"
            " </b><code>{}</code><b> is now {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Command not found</b>"
        ),
        "inline_settings": "⚙️ <b>Here you can configure your acbot settings</b>",
        "confirm_update": (
            "🧭 <b>Please, confirm that you want to update. Your userbot will be"
            " restarted</b>"
        ),
        "confirm_restart": "🔄 <b>Please, confirm that you want to restart</b>",
        "suggest_fs": "✅ Suggest FS for modules",
        "do_not_suggest_fs": "🚫 Suggest FS for modules",
        "use_fs": "✅ Always use FS for modules",
        "do_not_use_fs": "🚫 Always use FS for modules",
        "btn_restart": "🔄 Restart",
        "btn_update": "🧭 Update",
        "close_menu": "😌 Close menu",
        "custom_emojis": "✅ Custom emojis",
        "no_custom_emojis": "🚫 Custom emojis",
        "suggest_subscribe": "✅ Suggest subscribe to channel",
        "do_not_suggest_subscribe": "🚫 Suggest subscribe to channel",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>This command must be"
            " executed in chat</b>"
        ),
        "nonick_warning": (
            "Warning! You enabled NoNick with default prefix! "
            "You may get muted in acbot chats. Change prefix or "
            "disable NoNick!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Reply to a message"
            " of user, which needs to be added to NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>This action will fully remove acbot from this account and can't be"
            " reverted!</b>\n\n<i>- acbot chats will be removed\n- Session will be"
            " terminated and removed\n- acbot inline bot will be removed</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Are you really sure you want to delete acbot?</b>"
        ),
        "deauth_yes": "I'm sure",
        "deauth_no_1": "I'm not sure",
        "deauth_no_2": "I'm uncertain",
        "deauth_no_3": "I'm struggling to answer",
        "deauth_cancel": "🚫 Cancel",
        "deauth_confirm_btn": "😢 Delete",
        "uninstall": "😢 <b>Uninstalling acbot...</b>",
        "uninstalled": (
            "😢 <b>acbot uninstalled. Web interface is still active, you can add another"
            " account</b>"
        ),
        "logs_cleared": "🗑 <b>Logs cleared</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these commands:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these users:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these chats:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Nothing to"
            " show...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>This command gives access to your acbot web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>. Type"
            " </b><code>{}proxypass force_insecure</code><b> to ignore this warning</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>This command gives access to your acbot web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Opening tunnel to acbot web interface...</b>",
        "tunnel_opened": "🎉 <b>Tunnel opened. This link is valid for about 1 hour</b>",
        "web_btn": "🌍 Web interface",
        "btn_yes": "🚸 Open anyway",
        "btn_no": "🔻 Cancel",
        "authorhost_web": (
            "✌️ <b>This link leads to WebSite of Author. You can read information about Author and donate him</b>"
        ),
        "disable_stats": "✅ Anonymous stats allowed",
        "enable_stats": "🚫 Anonymous stats disabled",
    }

    strings_ua = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Глядачі:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Глядача {} не"
            " знайдено</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Глядач {} тепер"
            " <u>вимкнено</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Глядач {} тепер"
            " <u>ввімкнено</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Вкажи ім`я"
            " глядача</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Стан NoNick для"
            " цього користувача: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Вкажи команду, для"
            " якої треба ввімкнути\\вимкнути NoNick</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Стан NoNick для"
            " </b><code>{}</code><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Команду не знайдено</b>"
        ),
        "inline_settings": "⚙️ <b>Тут можна керувати налаштуваннями acbot</b>",
        "confirm_update": "🧭 <b>Підтвердіть оновлення. AuthorChe's буде перезавантажено</b>",
        "confirm_restart": "🔄 <b>Підтвердіть перезавантаження</b>",
        "suggest_fs": "✅ Пропонувати збереження модулів",
        "do_not_suggest_fs": "🚫 Пропонувати збереження модулів",
        "use_fs": "✅ Завжди зберігати модулі",
        "do_not_use_fs": "🚫 Завжди зберігати модулі",
        "btn_restart": "🔄 Перезавантаження",
        "btn_update": "🧭 Оновлення",
        "close_menu": "😌 Закрити меню",
        "custom_emojis": "✅ Кастомні емодзі",
        "no_custom_emojis": "🚫 Кастомні емодзі",
        "suggest_subscribe": "✅ Пропонувати підписуватися на канал",
        "do_not_suggest_subscribe": "🚫 Пропонувати підписуватися на канал",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Цю команду потрібно"
            " виконувати в чаті</b>"
        ),
        "_cls_doc": "Додаткові налаштування acbot",
        "nonick_warning": (
            "Увага! Ти ввімкнув NoNick зі стандартним префіксом! "
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Напиши в відповідь на повідомлення"
            " користувача, для якого потрібно ввімкнути NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>Ця дія повністю видалить AuthorBot з цього аккаунту! Його не можна"
            " відмінити</b>\n\n<i>- Всі чати, зв`язані з acbot буде видалено\n- Сесію"
            " acbot буде скинуто\n- Інлайн бот acbot буде видалено</i>"
        ),
        "deauth_confirm_step2": "⚠️ <b>Ти точно вевнений, що хочеш видалити acbot?</b>",
        "deauth_yes": "Я впевнений",
        "deauth_no_1": "Я не впевнений",
        "deauth_no_2": "Не точно",
        "deauth_no_3": "Ні",
        "deauth_cancel": "🚫 Відміна",
        "deauth_confirm_btn": "😢 Видалити",
        "uninstall": "😢 <b>Видаляю acbot...</b>",
        "uninstalled": (
            "😢 <b>acbot видалено. Веб-інтерфейс все ще активний, можна додати інші"
            " аккаунти!</b>"
        ),
        "logs_cleared": "🗑 <b>Логи очищено</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick ввімкнено для"
            " цих команд:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick ввімкнено для"
            " цих пользователей:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick вимкнено для"
            " циє чатів:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Немає що"
            " показувати...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Ця команда дає доступ до веб-інтерфейсу acbot. Її виконання в"
            " публічних чатах є загрозою безпеки. Краще виконувати"
            " її в <a href='tg://openmessage?user_id={}'>Особистих повідомленнях</a>."
            " Виконай </b><code>{}proxypass force_insecure</code><b> щоб вимкнути"
            " це попередження</b>"
        ),
        "privacy_leak_nowarn": (
           "⚠️ <b>Ця команда дає доступ до веб-інтерфейсу acbot. Її виконання в"
            " публічних чатах є загрозою безпеки. Краще виконувати"
            " її в <a href='tg://openmessage?user_id={}'>Особистих повідомленнях</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Відкриваю тонель до веб-інтерфейсу acbot...</b>",
        "tunnel_opened": (
            "🎉 <b>Тонель відчинено. Це посилання буде активним не більше години</b>"
        ),
        "web_btn": "🌍 Веб-інтерфейс",
        "btn_yes": "🚸 Все одно відкрити",
        "btn_no": "🔻 Закрити",
        "Authorhost_web": (
            "✌️ <b>По цьому посиланню ти потрапиш на"
            " вебсайт власника боту. Там ти можеш прочитати інформацію про Автора та зробити пожертвування на розвиток проекту</b>"
        ),
        "disable_stats": "✅ Просто кнопочка :)",
        "enable_stats": "🚫 Просто кнопочка :)",
    }

    def get_watchers(self) -> tuple:
        return [
            str(watcher.__self__.__class__.strings["name"])
            for watcher in self.allmodules.watchers
            if watcher.__self__.__class__.strings is not None
        ], self._db.get(main.__name__, "disabled_watchers", {})

    async def _uninstall(self, call: InlineCall):
        await call.edit(self.strings("uninstall"))

        async with self._client.conversation("@BotFather") as conv:
            for msg in [
                "/deletebot",
                f"@{self.inline.bot_username}",
                "Yes, I am totally sure.",
            ]:
                m = await conv.send_message(msg)
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

                await m.delete()
                await r.delete()

        async for dialog in self._client.iter_dialogs(
            None,
            ignore_migrated=True,
        ):
            if (
                dialog.name
                in {
                    "logs",
                    "onload",
                    "assets",
                    "backups",
                    "acc-switcher",
                    "silent-tags",
                }
                and dialog.is_channel
                and (
                    dialog.entity.participants_count == 1
                    or dialog.entity.participants_count == 2
                    and dialog.name in {"logs", "silent-tags"}
                )
                or (
                    self._client.loader.inline.init_complete
                    and dialog.entity.id == self._client.loader.inline.bot_id
                )
            ):
                await self._client.delete_dialog(dialog.entity)

        folders = await self._client(GetDialogFiltersRequest())

        if any(folder.title == "acbot" for folder in folders):
            folder_id = max(
                folders,
                key=lambda x: x.id,
            ).id

            await self._client(UpdateDialogFilterRequest(id=folder_id))

        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.CRITICAL)

        await self._client.log_out()

        await call.edit(self.strings("uninstalled"))

        if "AUTHORHOST" in os.environ:
            os.system("authorhost restart")
            return

        atexit.register(restart, *sys.argv[1:])
        sys.exit(0)

    async def _uninstall_confirm_step_2(self, call: InlineCall):
        await call.edit(
            self.strings("deauth_confirm_step2"),
            utils.chunks(
                list(
                    sorted(
                        [
                            {
                                "text": self.strings("deauth_yes"),
                                "callback": self._uninstall,
                            },
                            *[
                                {
                                    "text": self.strings(f"deauth_no_{i}"),
                                    "action": "close",
                                }
                                for i in range(1, 4)
                            ],
                        ],
                        key=lambda _: random.random(),
                    )
                ),
                2,
            )
            + [
                [
                    {
                        "text": self.strings("deauth_cancel"),
                        "action": "close",
                    }
                ]
            ],
        )

    @loader.owner
    @loader.command(ua_doc="Видалити acbot")
    async def uninstall_acbot(self, message: Message):
        """Uninstall acbot"""
        await self.inline.form(
            self.strings("deauth_confirm"),
            message,
            [
                {
                    "text": self.strings("deauth_confirm_btn"),
                    "callback": self._uninstall_confirm_step_2,
                },
                {"text": self.strings("deauth_cancel"), "action": "close"},
            ],
        )

    @loader.command(ua_doc="Очистити логи")
    async def clearlogs(self, message: Message):
        """Clear logs"""
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    @loader.command(ua_doc="Показати активні глядачі")
    async def watchers(self, message: Message):
        """List current watchers"""
        watchers, disabled_watchers = self.get_watchers()
        watchers = [
            f"♻️ {watcher}"
            for watcher in watchers
            if watcher not in list(disabled_watchers.keys())
        ]
        watchers += [f"💢 {k} {v}" for k, v in disabled_watchers.items()]
        await utils.answer(
            message, self.strings("watchers").format("\n".join(watchers))
        )

    @loader.command(ua_doc="<module> - Ввімкнути/вимкнути глядач в даному чаті")
    async def watcherbl(self, message: Message):
        """<module> - Toggle watcher in current chat"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in map(lambda x: x.lower(), watchers):
            await utils.answer(message, self.strings("mod404").format(args))
            return

        args = next((x.lower() == args.lower() for x in watchers), False)

        current_bl = [
            v for k, v in disabled_watchers.items() if k.lower() == args.lower()
        ]
        current_bl = current_bl[0] if current_bl else []

        chat = utils.get_chat_id(message)
        if chat not in current_bl:
            if args in disabled_watchers:
                for k in disabled_watchers:
                    if k.lower() == args.lower():
                        disabled_watchers[k].append(chat)
                        break
            else:
                disabled_watchers[args] = [chat]

            await utils.answer(
                message,
                self.strings("disabled").format(args) + " <b>in current chat</b>",
            )
        else:
            for k in disabled_watchers.copy():
                if k.lower() == args.lower():
                    disabled_watchers[k].remove(chat)
                    if not disabled_watchers[k]:
                        del disabled_watchers[k]
                    break

            await utils.answer(
                message,
                self.strings("enabled").format(args) + " <b>in current chat</b>",
            )

        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)

    @loader.command(
        ua_doc=(
            "<модуль> - керування глобальними правилами глядача\n"
            "Аргументы:\n"
            "[-c - тільки в чатах]\n"
            "[-p - тільки в лс]\n"
            "[-o - тільки відправлені]\n"
            "[-i - тільки прийняті]"
        )
    )
    async def watchercmd(self, message: Message):
        """<module> - Toggle global watcher rules
        Args:
        [-c - only in chats]
        [-p - only in pm]
        [-o - only out]
        [-i - only incoming]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        chats, pm, out, incoming = False, False, False, False

        if "-c" in args:
            args = args.replace("-c", "").replace("  ", " ").strip()
            chats = True

        if "-p" in args:
            args = args.replace("-p", "").replace("  ", " ").strip()
            pm = True

        if "-o" in args:
            args = args.replace("-o", "").replace("  ", " ").strip()
            out = True

        if "-i" in args:
            args = args.replace("-i", "").replace("  ", " ").strip()
            incoming = True

        if chats and pm:
            pm = False
        if out and incoming:
            incoming = False

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [watcher.lower() for watcher in watchers]:
            return await utils.answer(message, self.strings("mod404").format(args))

        args = [watcher for watcher in watchers if watcher.lower() == args.lower()][0]

        if chats or pm or out or incoming:
            disabled_watchers[args] = [
                *(["only_chats"] if chats else []),
                *(["only_pm"] if pm else []),
                *(["out"] if out else []),
                *(["in"] if incoming else []),
            ]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            await utils.answer(
                message,
                self.strings("enabled").format(args)
                + f" (<code>{disabled_watchers[args]}</code>)",
            )
            return

        if args in disabled_watchers and "*" in disabled_watchers[args]:
            await utils.answer(message, self.strings("enabled").format(args))
            del disabled_watchers[args]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            return

        disabled_watchers[args] = ["*"]
        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
        await utils.answer(message, self.strings("disabled").format(args))

    @loader.command(ua_doc="Ввімкнути NoNick для окремого користувача")
    async def nonickuser(self, message: Message):
        """Allow no nickname for certain user"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("reply_required"))
            return

        u = reply.sender_id
        if not isinstance(u, int):
            u = u.user_id

        nn = self._db.get(main.__name__, "nonickusers", [])
        if u not in nn:
            nn += [u]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("on"))
        else:
            nn = list(set(nn) - {u})
            await utils.answer(message, self.strings("user_nn").format("off"))

        self._db.set(main.__name__, "nonickusers", nn)

    @loader.command(ua_doc="Ввімкнути NoNick для окремого чату")
    async def nonickchat(self, message: Message):
        """Allow no nickname in certain chat"""
        if message.is_private:
            await utils.answer(message, self.strings("private_not_allowed"))
            return

        chat = utils.get_chat_id(message)

        nn = self._db.get(main.__name__, "nonickchats", [])
        if chat not in nn:
            nn += [chat]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - {chat})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickchats", nn)

    @loader.command(ua_doc="Ввімкнути NoNick для окремої команди")
    async def nonickcmdcmd(self, message: Message):
        """Allow certain command to be executed without nickname"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_cmd"))
            return

        if args not in self.allmodules.commands:
            await utils.answer(message, self.strings("cmd404"))
            return

        nn = self._db.get(main.__name__, "nonickcmds", [])
        if args not in nn:
            nn += [args]
            nn = list(set(nn))
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - {args})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickcmds", nn)

    @loader.command(ua_doc="Показати список активних NoNick команд")
    async def nonickcmds(self, message: Message):
        """Returns the list of NoNick commands"""
        if not self._db.get(main.__name__, "nonickcmds", []):
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("cmd_nn_list").format(
                "\n".join(
                    [
                        f"▫️ <code>{self.get_prefix()}{cmd}</code>"
                        for cmd in self._db.get(main.__name__, "nonickcmds", [])
                    ]
                )
            ),
        )

    @loader.command(ua_doc="Показати список активних NoNick користувачів")
    async def nonickusers(self, message: Message):
        """Returns the list of NoNick users"""
        users = []
        for user_id in self._db.get(main.__name__, "nonickusers", []).copy():
            try:
                user = await self._client.get_entity(user_id)
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickusers",
                    list(
                        (
                            set(self._db.get(main.__name__, "nonickusers", []))
                            - {user_id}
                        )
                    ),
                )

                logger.warning("User %s removed from nonickusers list", user_id)
                continue

            users += [
                '▫️ <b><a href="tg://user?id={}">{}</a></b>'.format(
                    user_id,
                    utils.escape_html(get_display_name(user)),
                )
            ]

        if not users:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(users)),
        )

    @loader.command(ua_doc="Показати список активных NoNick чатів")
    async def nonickchats(self, message: Message):
        """Returns the list of NoNick chats"""
        chats = []
        for chat in self._db.get(main.__name__, "nonickchats", []):
            try:
                chat_entity = await self._client.get_entity(int(chat))
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickchats",
                    list(
                        (set(self._db.get(main.__name__, "nonickchats", [])) - {chat})
                    ),
                )

                logger.warning("Chat %s removed from nonickchats list", chat)
                continue

            chats += [
                '▫️ <b><a href="{}">{}</a></b>'.format(
                    utils.get_entity_url(chat_entity),
                    utils.escape_html(get_display_name(chat_entity)),
                )
            ]

        if not chats:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(chats)),
        )

    async def inline__setting(self, call: InlineCall, key: str, state: bool = False):
        if callable(key):
            key()
            telethon.extensions.html.CUSTOM_EMOJIS = not main.get_config_key(
                "disable_custom_emojis"
            )
        else:
            self._db.set(main.__name__, key, state)

        if key == "no_nickname" and state and self.get_prefix() == ".":
            await call.answer(
                self.strings("nonick_warning"),
                show_alert=True,
            )
        else:
            await call.answer("Configuration value saved!")

        await call.edit(
            self.strings("inline_settings"),
            reply_markup=self._get_settings_markup(),
        )

    async def inline__update(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_update"),
                reply_markup=[
                    {"text": "🪂 Update", "callback": self.inline__update},
                    {"text": "🚫 Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being updated...", show_alert=True)
        await call.delete()
        m = await self._client.send_message("me", f"{self.get_prefix()}update --force")
        await self.allmodules.commands["update"](m)

    async def inline__restart(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_restart"),
                reply_markup=[
                    {"text": "🔄 Restart", "callback": self.inline__restart},
                    {"text": "🚫 Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being restarted...", show_alert=True)
        await call.delete()
        await self.allmodules.commands["restart"](
            await self._client.send_message("me", f"{self.get_prefix()}restart --force")
        )

    def _get_settings_markup(self) -> list:
        return [
            [
                (
                    {
                        "text": "✅ NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "no_nickname", False)
                    else {
                        "text": "🚫 NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "grep", False)
                    else {
                        "text": "🚫 Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "inlinelogs", True)
                    else {
                        "text": "🚫 InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("do_not_suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        False,
                    ),
                }
                if self._db.get(main.__name__, "disable_modules_fs", False)
                else {
                    "text": self.strings("suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        True,
                    ),
                }
            ],
            [
                (
                    {
                        "text": self.strings("use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "permanent_modules_fs", False)
                    else {
                        "text": self.strings("do_not_use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "suggest_subscribe", True)
                    else {
                        "text": self.strings("do_not_suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("no_custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key(
                                "disable_custom_emojis", False
                            ),
                        ),
                    }
                    if main.get_config_key("disable_custom_emojis")
                    else {
                        "text": self.strings("custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key("disable_custom_emojis", True),
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("disable_stats"),
                        "callback": self.inline__setting,
                        "args": ("stats", False),
                    }
                    if self._db.get(main.__name__, "stats", True)
                    else {
                        "text": self.strings("enable_stats"),
                        "callback": self.inline__setting,
                        "args": (
                            "stats",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("btn_restart"),
                    "callback": self.inline__restart,
                    "args": (True,),
                },
                {
                    "text": self.strings("btn_update"),
                    "callback": self.inline__update,
                    "args": (True,),
                },
            ],
            [{"text": self.strings("close_menu"), "action": "close"}],
        ]

    @loader.owner
    @loader.command(ua_doc="Показати налаштування")
    async def settings(self, message: Message):
        """Show settings menu"""
        await self.inline.form(
            self.strings("inline_settings"),
            message=message,
            reply_markup=self._get_settings_markup(),
        )

    @loader.owner
    @loader.command(ua_doc="Відкрити тонель до веб-інтерфейсу acbot")
    async def weburl(self, message: Message, force: bool = False):
        """Opens web tunnel to your acbot web interface"""
        if "AUTHORHOST" in os.environ:
            form = await self.inline.form(
                self.strings("authorhost_web"),
                message=message,
                reply_markup={
                    "text": self.strings("web_btn"),
                    "url": await main.acbot.web.get_url(proxy_pass=False),
                },
                gif="https://t.me/authorche/137",
            )
            return

        if (
            not force
            and not message.is_private
            and "force_insecure" not in message.raw_text.lower()
        ):
            try:
                if not await self.inline.form(
                    self.strings("privacy_leak_nowarn").format(self._client.tg_id),
                    message=message,
                    reply_markup=[
                        {
                            "text": self.strings("btn_yes"),
                            "callback": self.weburl,
                            "args": (True,),
                        },
                        {"text": self.strings("btn_no"), "action": "close"},
                    ],
                    gif="https://i.gifer.com/embedded/download/Z5tS.gif",
                ):
                    raise Exception
            except Exception:
                await utils.answer(
                    message,
                    self.strings("privacy_leak").format(
                        self._client.tg_id,
                        self.get_prefix(),
                    ),
                )

            return

        if force:
            form = message
            await form.edit(
                self.strings("opening_tunnel"),
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )
        else:
            form = await self.inline.form(
                self.strings("opening_tunnel"),
                message=message,
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )

        url = await main.acbot.web.get_url(proxy_pass=True)

        await form.edit(
            self.strings("tunnel_opened"),
            reply_markup={"text": self.strings("web_btn"), "url": url},
            gif="https://t.me/authorche/137",
        )

    @loader.loop(interval=1, autostart=True)
    async def loop(self):
        obj = self.allmodules.get_approved_channel
        if not obj:
            return

        channel, event = obj

        try:
            await self._client(JoinChannelRequest(channel))
        except Exception:
            logger.exception("Failed to join channel")
            event.status = False
            event.set()
        else:
            event.status = True
            event.set()

    def _get_all_IDM(self, module: str):
        return {
            getattr(getattr(self.lookup(module), name), "name", name): getattr(
                self.lookup(module), name
            )
            for name in dir(self.lookup(module))
            if getattr(getattr(self.lookup(module), name), "is_debug_method", False)
        }

    @loader.command()
    async def invoke(self, message: Message):
        """<module or `core` for built-in methods> <method> - Only for debugging purposes. DO NOT USE IF YOU'RE NOT A DEVELOPER
        """
        args = utils.get_args_raw(message)
        if not args or len(args.split()) < 2:
            await utils.answer(message, self.strings("no_args"))
            return

        module = args.split()[0]
        method = args.split(maxsplit=1)[1]

        if module != "core" and not self.lookup(module):
            await utils.answer(message, self.strings("module404").format(module))
            return

        if (
            module == "core"
            and method not in ALL_INVOKES
            or module != "core"
            and method not in self._get_all_IDM(module)
        ):
            await utils.answer(message, self.strings("invoke404").format(method))
            return

        message = await utils.answer(
            message, self.strings("invoking").format(method, module)
        )
        result = ""

        if module == "core":
            if method == "clear_entity_cache":
                result = (
                    f"Dropped {len(self._client._acbot_entity_cache)} cache records"
                )
                self._client._acbot_entity_cache = {}
            elif method == "clear_fulluser_cache":
                result = (
                    f"Dropped {len(self._client._acbot_fulluser_cache)} cache records"
                )
                self._client._acbot_fulluser_cache = {}
            elif method == "clear_fullchannel_cache":
                result = (
                    f"Dropped {len(self._client._acbot_fullchannel_cache)} cache"
                    " records"
                )
                self._client._acbot_fullchannel_cache = {}
            elif method == "clear_perms_cache":
                result = f"Dropped {len(self._client._acbot_perms_cache)} cache records"
                self._client._acbot_perms_cache = {}
            elif method == "clear_cache":
                result = (
                    f"Dropped {len(self._client._acbot_entity_cache)} entity cache"
                    " records\nDropped"
                    f" {len(self._client._acbot_fulluser_cache)} fulluser cache"
                    " records\nDropped"
                    f" {len(self._client._acbot_fullchannel_cache)} fullchannel cache"
                    " records"
                )
                self._client._acbot_entity_cache = {}
                self._client._acbot_fulluser_cache = {}
                self._client._acbot_fullchannel_cache = {}
            elif method == "reload_core":
                core_quantity = await self.lookup("loader").reload_core()
                result = f"Reloaded {core_quantity} core modules"
            elif method == "inspect_cache":
                result = (
                    "Entity cache:"
                    f" {len(self._client._acbot_entity_cache)} records\nFulluser cache:"
                    f" {len(self._client._acbot_fulluser_cache)} records\nFullchannel"
                    f" cache: {len(self._client._acbot_fullchannel_cache)} records"
                )
            elif method == "inspect_modules":
                result = (
                    "Loaded modules: {}\nLoaded core modules: {}\nLoaded user"
                    " modules: {}"
                ).format(
                    len(self.allmodules.modules),
                    sum(
                        module.__origin__.startswith("<core")
                        for module in self.allmodules.modules
                    ),
                    sum(
                        not module.__origin__.startswith("<core")
                        for module in self.allmodules.modules
                    ),
                )
        else:
            result = await self._get_all_IDM(module)[method](message)

        await utils.answer(
            message,
            self.strings("invoke").format(method, utils.escape_html(result)),
        )
