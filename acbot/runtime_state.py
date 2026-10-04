# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

"""Dependency state belongs to the interpreter, not to a shared checkout."""

import hashlib
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def requirements_hash() -> str:
    return hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()


def state_path() -> Path:
    if sys.prefix == sys.base_prefix:
        interpreter = hashlib.sha256(str(Path(sys.executable).resolve()).encode()).hexdigest()[:16]
        cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        return cache / "authorbot" / interpreter / ".authorbot-requirements.sha256"
    return Path(sys.prefix) / ".authorbot-requirements.sha256"


def dependencies_ready() -> bool:
    try:
        return state_path().read_text(encoding="utf-8").strip() == requirements_hash()
    except FileNotFoundError:
        return False


def mark_dependencies_ready() -> None:
    """Called only after installing and validating this environment's packages."""
    path = state_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(requirements_hash() + "\n")
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
