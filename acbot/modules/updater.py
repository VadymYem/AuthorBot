
#              © Copyright 2022
#           https://t.me/authorche
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import atexit
import contextlib
import logging
import os
import subprocess
import sys
import time
import typing

import git
from git import GitCommandError, Repo

from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter, Message
from telethon.extensions.html import CUSTOM_EMOJIS

from .. import loader, utils, main, version

from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Updates itself"""

    strings = {
        "name": "Updater",
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Read the source code"
            " from</b> <a href='{}'>here</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Downloading"
            " updates...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Installing"
            " updates...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Restart successful!"
            " {}</b>\n<i>But still loading modules...</i>\n<i>Restart took {}s</i>"
        ),
        "origin_cfg_doc": "Git origin URL, for where to update from",
        "btn_restart": "🔄 Restart",
        "btn_update": "🧭 Update",
        "restart_confirm": "❓ <b>Are you sure you want to restart?</b>",
        "secure_boot_confirm": (
            "❓ <b>Are you sure you want to restart in secure boot mode?</b>"
        ),
        "update_confirm": (
            "❓ <b>Are you sure you"
            " want to update?\n\n<a"
            ' href="https://github.com/VadymYem/AuthorBot/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/VadymYem/AuthorBot/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>You are on the latest version, pull updates anyway?</b>",
        "cancel": "🚫 Cancel",
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Your {} is"
            " updating...</b>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>Userbot is fully"
            " loaded! {}</b>\n<i>Full restart took {}s</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Secure boot completed! {}</b>\n<i>Restart took {}s</i>"
        ),
    }

    strings_ua = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>мій код можна"
            " прочитати</b> <a href='{}'>тут</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>AuthorChe's"
            " перезавантажується...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Завантаження"
            " оновлень...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Встановлення"
            " оновлень...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Перезавантаження"
            " успішне! {}</b>\n<i>Але код ще завантажується...</i>\n<i>Перезавантаження"
            " зайняло {} секунд</i>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>AuthorChe's повністю"
            " завантажено! {}</b>\n<i>Повне перезавантаження зайняло {} секунд</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Безпечний запуск завершено! {}</b>\n<i>Перезавантаження зайняло {}"
            " сек</i>"
        ),
        "origin_cfg_doc": "Посилання, з якого будуть завантажуватися оновлення",
        "btn_restart": "🔄 Перезавантажити",
        "btn_update": "🧭 Оновити",
        "restart_confirm": "❓ <b>Ти впевнений в цьому?</b>",
        "secure_boot_confirm": (
            "❓ <b>Ти впевнений, що"
            " хочеш перезапуск в безпечному режимі?</b>"
        ),
        "update_confirm": (
            "❓ <b>Ти впевнений, що"
            " хочеш оновити пакети??\n\n<a"
            ' href="https://github.com/VadymYem/AuthorBot/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/VadymYem/AuthorBot/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>В тебе остання версія. Оновити примусово?</b>",
        "cancel": "🚫 Відмінити",
        "_cls_doc": "Оновлює бот",
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Твій AuthorChe`s"
            " перезавантажується...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Твой AuthorChe`s"
            " оновлюється...</b>"
        ),
        "heroku_update": (
            "♓️ <b>Оновляю Heroku...\nЦе може зайняти деякий час</b>"
        ),
        "heroku_update_done_nothing_to_push": (
            "😔 <b>Оновлення завершено. Нічого не змінилось, немає, що оновлювати...</b>"
        ),
    }

    @loader.owner
    @loader.command(ua_doc="Перезавантажує бот")
    async def restart(self, message: Message):
        """Restarts the userbot"""
        secure_boot = "--secure-boot" in utils.get_args_raw(message)
        try:
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or "-f" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings(
                        "secure_boot_confirm" if secure_boot else "restart_confirm"
                    ),
                    reply_markup=[
                        {
                            "text": self.strings("btn_restart"),
                            "callback": self.inline_restart,
                            "args": (secure_boot,),
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.restart_common(message, secure_boot)

    async def inline_restart(self, call: InlineCall, secure_boot: bool = False):
        await self.restart_common(call, secure_boot=secure_boot)

    async def process_restart_message(self, msg_obj: typing.Union[InlineCall, Message]):
        self.set(
            "selfupdatemsg",
            msg_obj.inline_message_id
            if hasattr(msg_obj, "inline_message_id")
            else f"{utils.get_chat_id(msg_obj)}:{msg_obj.id}",
        )

    async def restart_common(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        secure_boot: bool = False,
    ):
        if (
            hasattr(msg_obj, "form")
            and isinstance(msg_obj.form, dict)
            and "uid" in msg_obj.form
            and msg_obj.form["uid"] in self.inline._units
            and "message" in self.inline._units[msg_obj.form["uid"]]
        ):
            message = self.inline._units[msg_obj.form["uid"]]["message"]
        else:
            message = msg_obj

        if secure_boot:
            self._db.set(loader.__name__, "secure_boot", True)

        msg_obj = await utils.answer(
            msg_obj,
            self.strings("restarting_caption").format(
                utils.get_platform_emoji()
                if self._client.acbot_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "Acbot"
            )
            if "LAVHOST" not in os.environ
            else self.strings("lavhost_restart").format(
                '</b><emoji document_id="5192756799647785066">✌️</emoji><emoji'
                ' document_id="5193117564015747203">✌️</emoji><emoji'
                ' document_id="5195050806105087456">✌️</emoji><emoji'
                ' document_id="5195457642587233944">✌️</emoji><b>'
                if self._client.acbot_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "lavHost"
            ),
        )

        await self.process_restart_message(msg_obj)

        self.set("restart_ts", time.time())

        await self._db.remote_force_save()

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        with contextlib.suppress(Exception):
            await main.acbot.web.stop()

        atexit.register(restart, *sys.argv[1:])
        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)

        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()
        sys.exit(0)

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False

    @staticmethod
    def req_common():
        # Now we have downloaded new code, install requirements
        logger.debug("Installing new requirements...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(
                        os.path.dirname(utils.get_base_dir()),
                        "requirements.txt",
                    ),
                    "--user",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    @loader.command(ru_doc="Скачивает обновления юзербота")
    async def update(self, message: Message):
        """Downloads userbot updates"""
        try:
            current = utils.get_git_hash()
            upcoming = next(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            ).hexsha
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or "-f" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("update_confirm").format(
                        current, current[:8], upcoming, upcoming[:8]
                    )
                    if upcoming != current
                    else self.strings("no_update"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_update"),
                            "callback": self.inline_update,
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.inline_update(message)

    async def inline_update(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        hard: bool = False,
    ):
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")

        try:
            if "LAVHOST" in os.environ:
                msg_obj = await utils.answer(
                    msg_obj,
                    self.strings("lavhost_update").format(
                        "</b><emoji document_id=5192756799647785066>✌️</emoji><emoji"
                        " document_id=5193117564015747203>✌️</emoji><emoji"
                        " document_id=5195050806105087456>✌️</emoji><emoji"
                        " document_id=5195457642587233944>✌️</emoji><b>"
                        if self._client.acbot_me.premium
                        and CUSTOM_EMOJIS
                        and isinstance(msg_obj, Message)
                        else "lavHost"
                    ),
                )
                await self.process_restart_message(msg_obj)
                os.system("lavhost update")
                return

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("downloading"))
            req_update = await self.download_common()

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("installing"))
            if req_update:
                self.req_common()

            await self.restart_common(msg_obj)
        except GitCommandError:
            if not hard:
                await self.inline_update(msg_obj, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")
            return

    @loader.unrestricted
    @loader.command(ru_doc="Показать ссылку на исходный код проекта")
    async def source(self, message: Message):
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source").format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self):
        if self.get("selfupdatemsg") is not None:
            try:
                await self.update_complete()
            except Exception:
                logger.exception("Failed to complete update!")

        if self.get("do_not_create", False):
            return

        try:
            await self._add_folder()
        except Exception:
            logger.exception("Failed to add folder!")
        finally:
            self.set("do_not_create", True)

    async def _add_folder(self):
        folders = await self._client(GetDialogFiltersRequest())

        if any(getattr(folder, "title", None) == "acbot" for folder in folders):
            return

        try:
            folder_id = (
                max(
                    folders,
                    key=lambda x: x.id,
                ).id
                + 1
            )
        except ValueError:
            folder_id = 2

        try:
            await self._client(
                UpdateDialogFilterRequest(
                    folder_id,
                    DialogFilter(
                        folder_id,
                        title="acbot",
                        pinned_peers=(
                            [
                                await self._client.get_input_entity(
                                    self._client.loader.inline.bot_id
                                )
                            ]
                            if self._client.loader.inline.init_complete
                            else []
                        ),
                        include_peers=[
                            await self._client.get_input_entity(dialog.entity)
                            async for dialog in self._client.iter_dialogs(
                                None,
                                ignore_migrated=True,
                            )
                            if dialog.name
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
                                and dialog.entity.id
                                == self._client.loader.inline.bot_id
                            )
                            or dialog.entity.id
                            in [
                               1740714395,
                            ]  # official acbot chats
                        ],
                        emoticon="🐱",
                        exclude_peers=[],
                        contacts=False,
                        non_contacts=False,
                        groups=False,
                        broadcasts=False,
                        bots=False,
                        exclude_muted=False,
                        exclude_read=False,
                        exclude_archived=False,
                    ),
                )
            )
        except Exception:
            logger.critical(
                "Can't create acbot folder. Possible reasons are:\n"
                "- User reached the limit of folders in Telegram\n"
                "- User got floodwait\n"
                "Ignoring error and adding folder addition to ignore list"
            )

    async def update_complete(self):
        logger.debug("Self update successful! Edit message")
        start = self.get("restart_ts")
        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        msg = self.strings("success").format(utils.ascii_face(), took)
        ms = self.get("selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )

    async def full_restart_complete(self, secure_boot: bool = False):
        start = self.get("restart_ts")

        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        self.set("restart_ts", None)

        ms = self.get("selfupdatemsg")
        msg = self.strings(
            "secure_boot_complete" if secure_boot else "full_success"
        ).format(utils.ascii_face(), took)

        if ms is None:
            return

        self.set("selfupdatemsg", None)

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            await asyncio.sleep(60)
            await self._client.delete_messages(chat_id, message_id)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )
