"""Entry point. Checks for user and starts main script"""

# ©️ Dan G. && AuthorChe
# This file is a part of AuthorBot Userbot
# 🌐 https://github.com/VadymYem/AuthorBot
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import getpass
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ._internal import restart


def get_data_root():
    for index, arg in enumerate(sys.argv):
        if arg == "--data-root" and index + 1 < len(sys.argv):
            return Path(sys.argv[index + 1]).expanduser()

        if arg.startswith("--data-root="):
            return Path(arg.split("=", maxsplit=1)[1]).expanduser()

    return Path(
        "/data"
        if "DOCKER" in os.environ
        else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )


def wipe_data():
    if not {"-w", "--wipe"} & set(sys.argv):
        return

    print(
        "Are you sure you want to completely delete all session files, "
        "their databases and modules? This action is irreversible [y/N]"
    )
    if input("> ").strip().lower() not in {"yes", "y"}:
        print("Cancelled")
        sys.exit(0)

    data_root = get_data_root()
    patterns = (
        "config.json",
        "config-*.json",
        "*.session",
        "*.session-journal",
        "api_token.txt",
    )
    dirs = ("loaded_modules", "sessions")
    removed = 0

    for pattern in patterns:
        for path in data_root.glob(pattern):
            if not path.is_file():
                continue

            path.unlink()
            removed += 1

    for dirname in dirs:
        path = data_root / dirname
        if not path.is_dir():
            continue

        shutil.rmtree(path)
        removed += 1

    print(f"Removed files: {removed}")
    sys.exit(0)


wipe_data()


def get_file_hash(filename):
    hasher = hashlib.sha256()
    try:
        with open(filename, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except FileNotFoundError:
        return None


def deps():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-q",
            "--disable-pip-version-check",
            "--no-warn-script-location",
            "-r",
            "requirements.txt",
        ],
        check=True,
        timeout=600,
        capture_output=True,
    )
    with open(".requirements_hash", "w") as f:
        f.write(get_file_hash("requirements.txt"))


if (
    getpass.getuser() == "root"
    and "--root" not in " ".join(sys.argv)
    and not {"-h", "--help"} & set(sys.argv)
    and all(trigger not in os.environ for trigger in {"DOCKER", "GOORM", "NO_SUDO"})
):
    print("🚫" * 15)
    print("You attempted to run AuthorBot on behalf of root user")
    print("Please, create a new user and restart script")
    print("If this action was intentional, pass --root argument instead")
    print("🚫" * 15)
    print()
    print("Type force_insecure to ignore this warning")
    print("Type no_sudo if your system has no sudo (Debian vibes)")
    inp = input("> ").lower()
    if inp != "force_insecure":
        sys.exit(1)
    elif inp == "no_sudo":
        os.environ["NO_SUDO"] = "1"
        print("Added NO_SUDO in your environment variables")
        restart()

if sys.version_info < (3, 8, 0):
    print("🚫 Error: you must use at least Python version 3.8.0")
elif __package__ != "acbot":  # In case they did python __main__.py
    print("🚫 Error: you cannot run this as a script; you must execute as a package")
else:
    try:
        import herokutl
    except Exception:
        pass
    else:
        try:
            import herokutl  # noqa: F811

            if tuple(map(int, herokutl.__version__.split("."))) < (2, 1, 0):
                raise ImportError
        except ImportError:
            print("🔄 Installing dependencies...")
            deps()
            restart()

    try:
        from . import log

        log.init()

        from . import main
    except ImportError as e:
        print(f"{str(e)}\n🔄 Attempting dependencies installation... Just wait ⏱")
        deps()
        restart()

    if "AUTHORBOT_DO_NOT_RESTART" in os.environ:
        del os.environ["AUTHORBOT_DO_NOT_RESTART"]

    if "AUTHORBOT_DO_NOT_RESTART2" in os.environ:
        del os.environ["AUTHORBOT_DO_NOT_RESTART2"]

    prev_hash = None
    if os.path.exists(".requirements_hash"):
        with open(".requirements_hash") as f:
            prev_hash = f.read().strip()

    if prev_hash != get_file_hash("requirements.txt"):
        print("🔄 Detected changes in requirements.txt, updating dependencies...")
        deps()
        restart()

    main.acbot.main()  # Execute main function
