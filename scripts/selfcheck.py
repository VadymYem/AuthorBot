#!/usr/bin/env python3
"""Preflight checks used by installers, Docker builds and self-updates."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def check_python() -> None:
    roots = (
        ROOT / "acbot",
        ROOT / "downloads" / "ai_mods",
        ROOT / "scripts",
    )
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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


def check_json() -> None:
    for relative in ("app.json",):
        path = ROOT / relative
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("top-level JSON value must be an object")
        except Exception as exc:
            ERRORS.append(f"JSON: {relative}: {exc}")


def check_shell() -> None:
    bash = shutil.which("bash")
    if not bash:
        return
    for relative in ("install.sh", "termux.sh", "banner.sh", "docker.sh"):
        path = ROOT / relative
        if not path.exists():
            continue
        result = subprocess.run(
            [bash, "-n", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            output = (result.stderr or result.stdout).strip()
            ERRORS.append(f"Shell: {relative}: {output}")



def check_brand_assets() -> None:
    for relative in (
        "assets/acbot_pfp.jpg",
        "assets/bot_pfp.jpg",
    ):
        path = ROOT / relative
        if not path.is_file():
            ERRORS.append(f"Missing branding asset: {relative}")
            continue

        try:
            data = path.read_bytes()
        except OSError as exc:
            ERRORS.append(f"Branding asset: {relative}: {exc}")
            continue

        if len(data) < 4096:
            ERRORS.append(f"Branding asset is unexpectedly small: {relative}")
        if not data.startswith(b"\xff\xd8"):
            ERRORS.append(f"Branding asset is not a JPEG: {relative}")
        if not data.endswith(b"\xff\xd9"):
            ERRORS.append(f"Branding asset is truncated: {relative}")

    svg = ROOT / "assets" / "authorbot_banner.svg"
    try:
        svg_text = svg.read_text(encoding="utf-8")
        if "<svg" not in svg_text or "</svg>" not in svg_text:
            ERRORS.append("Branding SVG is invalid: assets/authorbot_banner.svg")
    except OSError as exc:
        ERRORS.append(f"Branding SVG: assets/authorbot_banner.svg: {exc}")


def check_required_files() -> None:
    for relative in (
        "requirements.txt",
        "assets/download.txt",
        "assets/bot_pfp.jpg",
        "assets/authorbot_banner.svg",
        "acbot/__main__.py",
        "acbot/inline/rich.py",
    ):
        if not (ROOT / relative).is_file():
            ERRORS.append(f"Missing required file: {relative}")


def main() -> int:
    check_python()
    check_yaml()
    check_json()
    check_shell()
    check_required_files()
    check_brand_assets()

    if ERRORS:
        print("AuthorBot self-check failed:", file=sys.stderr)
        for error in ERRORS:
            print(f" - {error}", file=sys.stderr)
        return 1

    print("AuthorBot self-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
