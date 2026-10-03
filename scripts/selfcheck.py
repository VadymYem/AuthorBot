#!/usr/bin/env python3
"""Static preflight checks for AuthorBot before startup/update."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def check_python() -> None:
    for path in sorted((ROOT / "acbot").rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
        except Exception as exc:
            ERRORS.append(f"Python: {path.relative_to(ROOT)}: {exc}")


def check_yaml() -> None:
    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False

    for path in sorted((ROOT / "acbot" / "langpacks").glob("*.yml")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.load(handle)
            if not isinstance(data, dict):
                raise TypeError("top-level YAML value must be a mapping")
        except Exception as exc:
            ERRORS.append(f"YAML: {path.relative_to(ROOT)}: {exc}")


def check_required_files() -> None:
    for relative in (
        "requirements.txt",
        "assets/download.txt",
        "assets/bot_pfp.png",
        "acbot/__main__.py",
    ):
        if not (ROOT / relative).exists():
            ERRORS.append(f"Missing required file: {relative}")


def main() -> int:
    check_python()
    check_yaml()
    check_required_files()

    if ERRORS:
        print("AuthorBot self-check failed:", file=sys.stderr)
        for error in ERRORS:
            print(f" - {error}", file=sys.stderr)
        return 1

    print("AuthorBot self-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
