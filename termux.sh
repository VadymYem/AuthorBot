#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-/dev/stdin}")" && pwd -P)"
PROFILE="${AUTHORBOT_PROFILE:-$HOME/.bash_profile}"
DISTRO="authorbot"
MARKER="# >>> AuthorBot autostart >>>"

if ! command -v pkg >/dev/null || [ -z "${PREFIX:-}" ]; then
  printf 'Цей інсталятор потрібно запускати у Termux.\n' >&2
  exit 2
fi
if [ ! -f "$APP_DIR/scripts/termux-runtime.sh" ] || [ ! -f "$APP_DIR/bootstrap-termux.sh" ]; then
  # The website also supports downloading/sourcing termux.sh by itself.
  # Keep stdin attached to the terminal; the script download uses a temp file.
  if [ -t 1 ]; then clear 2>/dev/null || printf '\033[2J\033[H'; fi
  LOG_FILE="${AUTHORBOT_LOG_FILE:-$HOME/authorbot-install.log}"
  printf 'AuthorBot by AuthorChe · Підготовка встановлення…\n'
  umask 077
  if ! { pkg update -y && pkg install -y curl; } >"$LOG_FILE" 2>&1; then
    printf 'Не вдалося підготувати Termux. Журнал: %s\n' "$LOG_FILE" >&2
    exit 1
  fi
  installer="$(mktemp "$PREFIX/tmp/authorbot-bootstrap.XXXXXX")"
  if ! curl -fsSL --retry 3 https://raw.githubusercontent.com/VadymYem/AuthorBot/main/bootstrap-termux.sh -o "$installer" 2>>"$LOG_FILE"; then
    rm -f "$installer"
    printf 'Не вдалося завантажити інсталятор. Журнал: %s\n' "$LOG_FILE" >&2
    exit 1
  fi
  export AUTHORBOT_LOG_FILE="$LOG_FILE" AUTHORBOT_LOG_INITIALIZED=1
  status=0
  bash "$installer" "$@" || status=$?
  rm -f "$installer"
  if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" != "$0" ]]; then
    return "$status"
  fi
  exit "$status"
fi

source "$APP_DIR/bootstrap-termux.sh"
ui_init
if [ -z "${AUTHORBOT_BOOTSTRAPPED:-}" ]; then
  ui_stage 1 '1/8 · Підготовка Termux'
  ui_run pkg update -y
  ui_run pkg install -y git proot-distro
  ui_stage 2 '2/8 · Перевірка AuthorBot'
fi

# OCI image tags are supported by PRoot-Distro 5 and newer.
# Some supported releases print help to stderr; capture both streams fully.
INSTALL_HELP="$(proot-distro install --help 2>&1 || true)"
if [[ "$INSTALL_HELP" != *"--name"* ]]; then
  printf 'Онови PRoot-Distro: pkg upgrade proot-distro\n' >&2
  exit 3
fi
ui_stage 3 '3/8 · Встановлення Debian'
CONTAINERS="$(proot-distro list --quiet 2>>"$LOG_FILE")"
if ! grep -Fxq "$DISTRO" <<< "$CONTAINERS"; then
  ui_run proot-distro install debian:bookworm --name "$DISTRO"
fi

# Source and session files stay in the existing Termux checkout.
# The guest has its own venv; the Termux Python version is irrelevant.
export AUTHORBOT_PROGRESS_FILE="$APP_DIR/.install-progress"
rm -f "$AUTHORBOT_PROGRESS_FILE"
ui_run proot-distro login --bind "$APP_DIR:/opt/authorbot" "$DISTRO" -- \
  /bin/bash /opt/authorbot/scripts/termux-runtime.sh install

ui_stage 8 '8/8 · Налаштування запуску'
LAUNCHER="$PREFIX/bin/authorbot"
{
  printf '#!%s/bin/bash\n' "$PREFIX"
  printf 'set -euo pipefail\n'
  printf 'APP_DIR=%q\n' "$APP_DIR"
  printf 'exec proot-distro login --bind "$APP_DIR:/opt/authorbot" authorbot -- /bin/bash /opt/authorbot/scripts/termux-runtime.sh run "$@"\n'
} >"$LAUNCHER"
chmod 700 "$LAUNCHER"

if [ -z "${NO_AUTOSTART:-}" ]; then
  # Replace only our old managed block and preserve all other profile content.
  python - "$PROFILE" "$MARKER" >>"$LOG_FILE" 2>&1 <<'PY'
import os
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
start = sys.argv[2]
end = "# <<< AuthorBot autostart <<<"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True) if path.exists() else []
kept = []
inside = False
for line in lines:
    if line.strip() == start:
        inside = True
    elif inside and line.strip() == end:
        inside = False
    elif not inside:
        kept.append(line)
if inside:
    raise RuntimeError("Незавершений блок AuthorBot у профілі; профіль не змінено")
block = '''
# >>> AuthorBot autostart >>>
if command -v authorbot >/dev/null 2>&1; then
  authorbot
fi
# <<< AuthorBot autostart <<<
'''
path.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
    temporary = Path(handle.name)
    handle.write("".join(kept).rstrip("\n") + "\n" + block)
try:
    if path.exists():
        temporary.chmod(path.stat().st_mode & 0o777)
    os.replace(temporary, path)
finally:
    temporary.unlink(missing_ok=True)
PY
fi

ui_finish
if [ -z "${AUTHORBOT_INSTALL_ONLY:-}" ]; then
  # Foreground exec preserves the terminal throughout setup and later restarts.
  exec "$LAUNCHER" "$@"
fi
