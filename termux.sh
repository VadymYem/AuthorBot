#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
LOG_FILE="${AUTHORBOT_LOG_FILE:-$HOME/authorbot-install.log}"
PROFILE="${AUTHORBOT_PROFILE:-$HOME/.bash_profile}"
DISTRO="authorbot"
MARKER="# >>> AuthorBot autostart >>>"

fail() {
  printf '\nПомилка встановлення. Журнал: %s\n' "$LOG_FILE" >&2
}
trap fail ERR
run() { "$@" 2>&1 | tee -a "$LOG_FILE"; }

if ! command -v pkg >/dev/null || [ -z "${PREFIX:-}" ]; then
  printf 'Цей інсталятор потрібно запускати у Termux.\n' >&2
  exit 2
fi
if [ ! -f "$APP_DIR/scripts/termux-runtime.sh" ]; then
  printf 'Потрібна повна копія репозиторію AuthorBot.\n' >&2
  exit 2
fi

: >"$LOG_FILE"
printf 'AuthorBot: Termux → Debian Bookworm → Python 3.11\n\n'
run pkg update -y
run pkg install -y git proot-distro

# OCI image tags are supported by PRoot-Distro 5 and newer.
if ! proot-distro install --help | grep -q -- '--name'; then
  printf 'Онови PRoot-Distro: pkg upgrade proot-distro\n' >&2
  exit 3
fi
if ! proot-distro list --quiet | grep -Fxq "$DISTRO"; then
  run proot-distro install debian:bookworm --name "$DISTRO"
fi

# Source and session files stay in the existing Termux checkout.
# The guest has its own venv; the Termux Python version is irrelevant.
run proot-distro login --bind "$APP_DIR:/opt/authorbot" "$DISTRO" -- \
  /bin/bash /opt/authorbot/scripts/termux-runtime.sh install

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
  python - "$PROFILE" "$MARKER" <<'PY'
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

printf '\nВстановлення завершено. Для наступного запуску: authorbot\n'
if [ -z "${AUTHORBOT_INSTALL_ONLY:-}" ]; then
  exec "$LAUNCHER" "$@"
fi
