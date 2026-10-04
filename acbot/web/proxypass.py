# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

import asyncio
import contextlib
import logging
import re
import typing

from .. import utils

logger = logging.getLogger(__name__)


class ProxyPasser:
    """Creates a temporary localhost.run reverse tunnel for the setup web UI."""

    def __init__(self, change_url_callback: callable = lambda _: None):
        self._tunnel_url = None
        self._sproc = None
        self._reader_tasks = []
        self._url_available = asyncio.Event()
        self._lock = asyncio.Lock()
        self._change_url_callback = change_url_callback

    async def _read_stream(self, stream: asyncio.StreamReader) -> None:
        while True:
            data = await stream.readline()
            if not data:
                return

            line = data.decode("utf-8", errors="replace").strip()
            if line:
                await self._process_stream(line)

    def kill(self):
        if self._sproc is None:
            return

        if self._sproc.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                self._sproc.terminate()

        for task in self._reader_tasks:
            task.cancel()
        self._reader_tasks = []
        self._sproc = None

    async def _process_stream(self, output_line: str) -> None:
        # Do not dump the whole SSH stream into logs. It may contain connection
        # metadata that is irrelevant after the tunnel URL is parsed.
        match = re.search(r"tunneled.*?(https://\S+)", output_line, re.IGNORECASE)
        if not match:
            return

        self._tunnel_url = match.group(1).rstrip()
        self._change_url_callback(self._tunnel_url)
        logger.debug("Proxy pass tunnel is ready")
        self._url_available.set()

    async def _start_process(self, port: int) -> None:
        self._url_available = asyncio.Event()
        self._sproc = await asyncio.create_subprocess_exec(
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ExitOnForwardFailure=yes",
            "-R",
            f"80:127.0.0.1:{port}",
            "nokey@localhost.run",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader_tasks = [
            asyncio.create_task(self._read_stream(self._sproc.stdout)),
            asyncio.create_task(self._read_stream(self._sproc.stderr)),
        ]
        utils.atexit(self.kill)

    async def get_url(self, port: int, no_retry: bool = False) -> typing.Optional[str]:
        async with self._lock:
            if self._tunnel_url and self._sproc is not None:
                if self._sproc.returncode is None:
                    return self._tunnel_url
                self.kill()
                self._tunnel_url = None

            attempts = 1 if no_retry else 2
            for _ in range(attempts):
                try:
                    await self._start_process(port)
                    await asyncio.wait_for(self._url_available.wait(), timeout=15)
                except (asyncio.TimeoutError, FileNotFoundError, OSError):
                    logger.warning("Unable to create setup reverse tunnel", exc_info=True)
                    self.kill()
                    self._tunnel_url = None
                    continue

                if self._tunnel_url:
                    return self._tunnel_url

            return None
