# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

import asyncio
import logging
import os
import random
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


async def fw_protect():
    await asyncio.sleep(random.randint(1000, 3000) / 1000)


def _restart_process(*_):
    os.chdir(ROOT)
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        "acbot",
        *sys.argv[1:],
    )


def get_startup_callback() -> callable:
    return _restart_process


def restart():
    if "--sandbox" in sys.argv:
        raise SystemExit(0)

    if "AUTHORBOT_DO_NOT_RESTART2" in os.environ:
        print(
            "Got in a restart loop. Remove conflicting packages manually and "
            "restart AuthorBot."
        )
        raise SystemExit(1)

    logging.getLogger().setLevel(logging.CRITICAL)
    print("🔄 Restarting...")

    if "LAVHOST" in os.environ:
        os.system("lavhost restart")
        return

    if "AUTHORBOT_DO_NOT_RESTART" not in os.environ:
        os.environ["AUTHORBOT_DO_NOT_RESTART"] = "1"
    else:
        os.environ["AUTHORBOT_DO_NOT_RESTART2"] = "1"

    # Replace only AuthorBot. Killing the process group also terminates the
    # Termux shell/PRoot supervisor and detaches the new process from stdin.
    _restart_process()


def clear_terminal():
    if not sys.stdout.isatty():
        return
    sys.stdout.flush()
    try:
        result = subprocess.run(["clear"], stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0:
            return
    except OSError:
        pass
    print("\033[2J\033[H", end="", flush=True)


def print_banner(banner: str):
    clear_terminal()
    path = ROOT / "assets" / banner
    print(path.read_text(encoding="utf-8"))


def print_running_banner(build: str, version: str, update_available: bool, language: str = "en"):
    from .public_pages import text

    clear_terminal()
    tty = sys.stdout.isatty()
    width = min(max(shutil.get_terminal_size((40, 24)).columns, 24), 60)
    def center(value):
        cells = sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)
        return " " * max(0, (width - cells) // 2) + value
    amber, green, dim, reset = ("\033[38;2;230;188;116m", "\033[1;32m", "\033[2m", "\033[0m") if tty else ("", "", "", "")
    logo = (ROOT / "assets" / "authorbot_logo.txt").read_text().splitlines()
    logo_padding = " " * max(0, (width - max(map(len, logo))) // 2)
    for line in logo:
        print(amber + logo_padding + line.rstrip() + reset)
    print("\n" + amber + center("AuthorBot") + reset)
    print(dim + center("by AuthorChe") + reset)
    print("\n" + green + center("● " + text("running", language)) + reset)
    print("\n" + center(f'{text("version", language)}: {version}'))
    print(center(f'{text("build", language)}: {build[:7]}'))
    print(center(text("update" if update_available else "current", language)))
    print()
    for label, url in (("authorche.top", "https://authorche.top"), ("t.me/wsinfo", "https://t.me/wsinfo"), ("VadymYem/AuthorBot", "https://github.com/VadymYem/AuthorBot")):
        padding = center(label)[:-len(label)]
        print(padding + f"\033]8;;{url}\033\\{label}\033]8;;\033\\" if tty else url)
    print(flush=True)
