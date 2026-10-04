# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# ©️ Dan G. && AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
import asyncio
import io
import json
import logging
import random
import time
import typing

from herokutl.tl import functions
from herokutl.tl.tlobject import TLRequest
from herokutl.tl.types import Message
from herokutl.utils import is_list_like

from .. import loader, utils
from ..inline.types import InlineCall
from ..web.debugger import WebDebugger

logger = logging.getLogger(__name__)

GROUPS = [
    "auth",
    "account",
    "users",
    "contacts",
    "messages",
    "updates",
    "photos",
    "upload",
    "help",
    "channels",
    "bots",
    "payments",
    "stickers",
    "phone",
    "langpack",
    "folders",
    "stats",
]


CONSTRUCTORS = {
    (lambda x: x[0].lower() + x[1:])(
        method.__class__.__name__.rsplit("Request", 1)[0]
    ): method.CONSTRUCTOR_ID
    for method in utils.array_sum(
        [
            [
                method
                for method in dir(getattr(functions, group))
                if isinstance(method, TLRequest)
            ]
            for group in GROUPS
        ]
    )
}


@loader.tds
class APIRatelimiterMod(loader.Module):
    """Helps userbot avoid spamming Telegram API"""

    strings = {"name": "APILimiter"}

    def __init__(self):
        self._ratelimiter: typing.List[tuple] = []
        self._suspend_until = 0
        self._lock = False
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "time_sample",
                15,
                lambda: self.strings("_cfg_time_sample"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "threshold",
                100,
                lambda: self.strings("_cfg_threshold"),
                validator=loader.validators.Integer(minimum=10),
            ),
            loader.ConfigValue(
                "local_floodwait",
                30,
                lambda: self.strings("_cfg_local_floodwait"),
                validator=loader.validators.Integer(minimum=10, maximum=3600),
            ),
            loader.ConfigValue(
                "forbidden_methods",
                ["joinChannel", "importChatInvite"],
                lambda: self.strings("_cfg_forbidden_methods"),
                validator=loader.validators.MultiChoice(
                    [
                        "sendReaction",
                        "joinChannel",
                        "importChatInvite",
                    ]
                ),
                on_change=lambda: self._client.forbid_constructors(
                    CONSTRUCTORS[name]
                    for name in self.config["forbidden_methods"]
                    if name in CONSTRUCTORS
                ),
            ),
        )

    async def client_ready(self):
        asyncio.ensure_future(self._install_protection())

    async def _install_protection(self):
        await asyncio.sleep(30)  # Restart lock
        if hasattr(self._client._call, "_old_call_rewritten"):
            raise loader.SelfUnload("Already installed")

        old_call = self._client._call

        async def new_call(
            sender: "MTProtoSender",  # type: ignore  # noqa: F821
            request: TLRequest,
            ordered: bool = False,
            flood_sleep_threshold: int = None,
        ):
            await asyncio.sleep(random.randint(1, 5) / 100)
            req = (request,) if not is_list_like(request) else request
            for r in req:
                if (
                    time.perf_counter() > self._suspend_until
                    and not self.get(
                        "disable_protection",
                        True,
                    )
                    and (
                        r.__module__.rsplit(".", maxsplit=1)[1]
                        in {"messages", "account", "channels"}
                    )
                ):
                    request_name = type(r).__name__
                    self._ratelimiter += [(request_name, time.perf_counter())]

                    self._ratelimiter = list(
                        filter(
                            lambda x: time.perf_counter() - x[1]
                            < int(self.config["time_sample"]),
                            self._ratelimiter,
                        )
                    )

                    if (
                        len(self._ratelimiter) > int(self.config["threshold"])
                        and not self._lock
                    ):
                        self._lock = True
                        report = io.BytesIO(
                            json.dumps(
                                self._ratelimiter,
                                indent=4,
                            ).encode()
                        )
                        report.name = "local_fw_report.json"

                        await self.inline.bot.send_document(
                            self.tg_id,
                            report,
                            caption=self.inline.sanitise_text(
                                self.strings("warning").format(
                                    self.config["local_floodwait"],
                                    prefix=utils.escape_html(self.get_prefix()),
                                )
                            ),
                        )

                        try:
                            await asyncio.sleep(int(self.config["local_floodwait"]))
                        finally:
                            self._lock = False

            return await old_call(sender, request, ordered, flood_sleep_threshold)

        self._client._call = new_call
        self._client._old_call_rewritten = old_call
        self._client._call._acbot_overwritten = True
        logger.debug("Successfully installed ratelimiter")

    async def on_unload(self):
        if hasattr(self._client, "_old_call_rewritten"):
            self._client._call = self._client._old_call_rewritten
            delattr(self._client, "_old_call_rewritten")
            logger.debug("Successfully uninstalled ratelimiter")

    @loader.command()
    async def suspend_api_protect(self, message: Message):
        if not (args := utils.get_args_raw(message)) or not args.isdigit():
            await utils.answer(message, self.strings("args_invalid"))
            return

        self._suspend_until = time.perf_counter() + int(args)
        await utils.answer(message, self.strings("suspended_for").format(args))

    @loader.command()
    async def api_fw_protection(self, message: Message):
        await self.inline.form(
            message=message,
            text=self.strings("u_sure"),
            reply_markup=[
                {"text": self.strings("btn_no"), "action": "close"},
                {"text": self.strings("btn_yes"), "callback": self._finish},
            ],
        )

    @property
    def _debugger(self) -> typing.Optional[WebDebugger]:
        handler = next(
            (
                handler
                for handler in logging.getLogger().handlers
                if hasattr(handler, "web_debugger")
            ),
            None,
        )
        return getattr(handler, "web_debugger", None)

    @loader.command()
    async def debugger(self, message: Message):
        """— show the local read-only traceback viewer, if enabled."""
        debugger = self._debugger
        if not debugger:
            await utils.answer(message, self.strings("debugger_disabled"))
            return

        await utils.answer(
            message,
            (
                "<b>🐞 Local traceback viewer</b>\n\n"
                f"<code>{utils.escape_html(debugger.url)}</code>\n"
                "<i>It is bound to 127.0.0.1 and does not allow Python evaluation.</i>"
            ),
        )

    async def _finish(self, call: InlineCall):
        state = self.get("disable_protection", True)
        self.set("disable_protection", not state)
        await call.edit(self.strings("on" if state else "off"))
