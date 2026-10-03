"""Entry point. Checks the runtime and starts AuthorBot."""

import getpass
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

from ._internal import restart
from .runtime_state import dependencies_ready, mark_dependencies_ready

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def get_data_root() -> Path:
    for index, arg in enumerate(sys.argv):
        if arg == "--data-root" and index + 1 < len(sys.argv):
            return Path(sys.argv[index + 1]).expanduser()

        if arg.startswith("--data-root="):
            return Path(arg.split("=", maxsplit=1)[1]).expanduser()

    return Path("/data" if "DOCKER" in os.environ else ROOT)


def wipe_data():
    if not {"-w", "--wipe"} & set(sys.argv):
        return

    print(
        "Are you sure you want to completely delete all session files, "
        "their databases and modules? This action is irreversible [y/N]"
    )
    if input("> ").strip().lower() not in {"yes", "y"}:
        print("Cancelled")
        raise SystemExit(0)

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
            if path.is_file():
                path.unlink()
                removed += 1

    for dirname in dirs:
        path = data_root / dirname
        if path.is_dir():
            shutil.rmtree(path)
            removed += 1

    print(f"Removed files: {removed}")
    raise SystemExit(0)


def deps() -> None:
    """Install core requirements into the interpreter that runs AuthorBot."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--disable-pip-version-check",
            "--no-warn-script-location",
            "-r",
            str(REQUIREMENTS),
        ],
        cwd=ROOT,
        check=False,
        timeout=600,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        print(result.stdout)
        raise RuntimeError("Dependency installation failed")

    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    mark_dependencies_ready()


def ensure_root_policy() -> None:
    if (
        getpass.getuser() != "root"
        or "--root" in sys.argv
        or {"-h", "--help"} & set(sys.argv)
        or any(trigger in os.environ for trigger in {"DOCKER", "GOORM", "NO_SUDO"})
    ):
        return

    print("🚫" * 15)
    print("You attempted to run AuthorBot as root.")
    print("Prefer a regular user, or pass --root if this is intentional.")
    print("Type force_insecure to continue, or no_sudo to suppress this check.")
    print("🚫" * 15)

    answer = input("> ").strip().lower()
    if answer == "no_sudo":
        os.environ["NO_SUDO"] = "1"
        restart()

    if answer != "force_insecure":
        raise SystemExit(1)


def ensure_dependencies() -> None:
    try:
        import herokutl
    except ModuleNotFoundError:
        print("🔄 Installing dependencies...")
        deps()
        restart()

    try:
        version = tuple(map(int, herokutl.__version__.split(".")))
    except Exception:
        version = (0, 0, 0)

    if version < (2, 1, 0):
        print("🔄 Updating HerokuTL and dependencies...")
        deps()
        restart()


wipe_data()
ensure_root_policy()

if sys.version_info < (3, 10):
    print("🚫 Error: AuthorBot requires Python 3.10 or newer.")
    raise SystemExit(1)

if __package__ != "acbot":
    print("🚫 Error: run AuthorBot as a package: python -m acbot")
    raise SystemExit(1)

ensure_dependencies()

try:
    from . import log

    log.init()

    from . import main
except ModuleNotFoundError:
    print("🔄 A Python dependency is missing; reinstalling core requirements...")
    deps()
    restart()
except ImportError:
    print("🚫 AuthorBot encountered an internal import error:")
    traceback.print_exc()
    raise SystemExit(1)

if not dependencies_ready():
    print("🔄 requirements.txt changed; updating dependencies...")
    deps()
    restart()

for flag in ("AUTHORBOT_DO_NOT_RESTART", "AUTHORBOT_DO_NOT_RESTART2"):
    os.environ.pop(flag, None)

try:
    main.acbot.main()
except EOFError:
    print("\nВвід у терміналі закрито. Запусти authorbot у відкритому Termux, щоб продовжити вхід.")
    raise SystemExit(2)
