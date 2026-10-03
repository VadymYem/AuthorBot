"""Responsible for web init and mandatory ops"""

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import base64
import contextlib
import hmac
import inspect
import logging
import os
import secrets
import subprocess

import aiohttp_jinja2
import jinja2
from aiohttp import web

from ..database import Database
from ..loader import Modules
from ..tl_cache import CustomTelegramClient
from . import proxypass, root

logger = logging.getLogger(__name__)


class Web(root.Web):
    def __init__(self, **kwargs):
        self.runner = None
        self.port = None
        self.running = asyncio.Event()
        self.ready = asyncio.Event()
        self.client_data = {}
        self._setup_web_user = os.environ.get("AUTHORBOT_WEB_USER", "authorbot")
        self._setup_web_password = os.environ.get("AUTHORBOT_WEB_PASSWORD") or secrets.token_urlsafe(18)

        if "AUTHORBOT_WEB_PASSWORD" not in os.environ:
            print(
                "\n🔐 First-run AuthorBot web authentication\n"
                f"User: {self._setup_web_user}\n"
                f"Password: {self._setup_web_password}\n"
                "Set AUTHORBOT_WEB_USER/AUTHORBOT_WEB_PASSWORD to choose fixed credentials.\n"
            )

        @web.middleware
        async def first_setup_auth(request, handler):
            # Once at least one Telegram account is initialized, AuthorBot's
            # Telegram-confirmation flow is the primary authorization layer.
            if self.client_data:
                return await handler(request)

            header = request.headers.get("Authorization", "")
            if header.startswith("Basic "):
                try:
                    decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
                    username, password = decoded.split(":", 1)
                except (ValueError, UnicodeDecodeError):
                    username = password = ""

                if hmac.compare_digest(username, self._setup_web_user) and hmac.compare_digest(
                    password,
                    self._setup_web_password,
                ):
                    return await handler(request)

            return web.Response(
                status=401,
                text="AuthorBot setup authentication required",
                headers={
                    "WWW-Authenticate": 'Basic realm="AuthorBot setup", charset="UTF-8"',
                    "Cache-Control": "no-store",
                },
            )

        self.app = web.Application(middlewares=[first_setup_auth])
        self.proxypasser = proxypass.ProxyPasser()
        aiohttp_jinja2.setup(
            self.app,
            filters={"getdoc": inspect.getdoc, "ascii": ascii},
            loader=jinja2.FileSystemLoader("web-resources"),
        )
        self.app["static_root_url"] = "/static"

        super().__init__(**kwargs)
        self.app.router.add_get("/favicon.ico", self.favicon)
        self.app.router.add_static("/static/", "web-resources/static")

    async def start_if_ready(
        self,
        total_count: int,
        port: int,
        proxy_pass: bool = False,
    ):
        if total_count <= len(self.client_data):
            if not self.running.is_set():
                await self.start(port, proxy_pass=proxy_pass)

            self.ready.set()

    async def get_url(self, proxy_pass: bool) -> str:
        url = None

        if all(option in os.environ for option in {"LAVHOST", "USER", "SERVER"}):
            return f"https://{os.environ['USER']}.{os.environ['SERVER']}.lavhost.ml"

        if proxy_pass:
            with contextlib.suppress(Exception):
                url = await asyncio.wait_for(
                    self.proxypasser.get_url(self.port),
                    timeout=10,
                )

        if not url:
            ip = (
                "127.0.0.1"
                if "DOCKER" not in os.environ
                else subprocess.run(
                    ["hostname", "-i"],
                    stdout=subprocess.PIPE,
                    check=True,
                )
                .stdout.decode("utf-8")
                .strip()
            )

            url = f"http://{ip}:{self.port}"

        self.url = url
        return url

    async def start(self, port: int, proxy_pass: bool = False):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.port = os.environ.get("PORT", port)
        site = web.TCPSite(self.runner, None, self.port)
        await site.start()

        await self.get_url(proxy_pass)

        self.running.set()

    async def stop(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        self.running.clear()
        self.ready.clear()

    async def add_loader(
        self,
        client: CustomTelegramClient,
        loader: Modules,
        db: Database,
    ):
        self.client_data[client.tg_id] = (loader, client, db)

    @staticmethod
    async def favicon(_):
        return web.Response(
            status=301,
            headers={"Location": "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg"},
        )
