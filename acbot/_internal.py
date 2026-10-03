import asyncio
import logging
import os
import random
import sys
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


def print_banner(banner: str):
    print("\033[2J\033[3;1f")
    path = ROOT / "assets" / banner
    print(path.read_text(encoding="utf-8"))
