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
from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web

from ..database import Database
from ..branding import BOT_PHOTO
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
        self._setup_web_user = os.environ.get("AUTHORBOT_WEB_USER", "authorbot").strip() or "authorbot"
        configured_password = os.environ.get("AUTHORBOT_WEB_PASSWORD", "").strip()
        self._setup_web_password = configured_password or secrets.token_urlsafe(18)

        if not configured_password:
            print(
                "\n🔐 First-run AuthorBot web authentication\n"
                f"User: {self._setup_web_user}\n"
                f"Password: {self._setup_web_password}\n"
                "Set AUTHORBOT_WEB_USER/AUTHORBOT_WEB_PASSWORD to choose fixed credentials.\n"
            )

        @web.middleware
        async def web_basic_auth(request, handler):
            # Web UI always stays behind Basic Auth. Telegram confirmation is an
            # additional authorization layer, not a replacement for HTTP auth.
            header = request.headers.get("Authorization", "")
            if header.startswith("Basic "):
                try:
                    decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
                    username, password = decoded.split(":", 1)
                except (ValueError, UnicodeDecodeError):
                    username = password = ""

                if hmac.compare_digest(username.encode("utf-8"), self._setup_web_user.encode("utf-8")) and hmac.compare_digest(
                    password.encode("utf-8"),
                    self._setup_web_password.encode("utf-8"),
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

        self.app = web.Application(middlewares=[web_basic_auth])
        self.proxypasser = proxypass.ProxyPasser()
        resources = Path(__file__).resolve().parents[2] / "web-resources"
        aiohttp_jinja2.setup(
            self.app,
            filters={"getdoc": inspect.getdoc, "ascii": ascii},
            loader=jinja2.FileSystemLoader(str(resources)),
        )
        self.app["static_root_url"] = "/static"

        super().__init__(**kwargs)
        self.app.router.add_get("/favicon.ico", self.favicon)
        self.app.router.add_get("/branding/bot.jpg", self.favicon)
        self.app.router.add_static("/static/", str(resources / "static"))

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
        explicit_url = os.environ.get("AUTHORBOT_PUBLIC_URL", "").strip()
        if explicit_url:
            self.url = explicit_url.rstrip("/")
            return self.url

        if all(option in os.environ for option in {"LAVHOST", "USER", "SERVER"}):
            self.url = f"https://{os.environ['USER']}.{os.environ['SERVER']}.lavhost.ml"
            return self.url

        if proxy_pass:
            try:
                url = await asyncio.wait_for(
                    self.proxypasser.get_url(self.port),
                    timeout=20,
                )
            except Exception:
                logger.warning("Unable to obtain reverse-tunnel URL", exc_info=True)
            else:
                if url:
                    self.url = url
                    return url

        host = os.environ.get("AUTHORBOT_WEB_BIND", "").strip()
        if not host:
            host = "0.0.0.0" if "DOCKER" in os.environ else "127.0.0.1"

        display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        self.url = f"http://{display_host}:{self.port}"
        return self.url

    async def start(self, port: int, proxy_pass: bool = False):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.port = os.environ.get("PORT", port)
        host = os.environ.get("AUTHORBOT_WEB_BIND", "").strip()
        if not host:
            host = "0.0.0.0" if "DOCKER" in os.environ else "127.0.0.1"

        site = web.TCPSite(self.runner, host, self.port)
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
        return web.FileResponse(BOT_PHOTO, headers={"Cache-Control": "public, max-age=3600"})
