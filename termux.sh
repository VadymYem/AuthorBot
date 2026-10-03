#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

APP_DIR="$HOME/AuthorBot"
REPO_URL="${AUTHORBOT_REPO_URL:-https://github.com/VadymYem/AuthorBot.git}"
LOG_FILE="$HOME/authorbot-install.log"
PROFILE="$HOME/.bash_profile"
MARKER="# >>> AuthorBot autostart >>>"

banner_bootstrap() {
  clear 2>/dev/null || true
  printf '\033[1;35m'
  printf '    _         _   _                 ____        _   \n'
  printf '   / \\  _   _| |_| |__   ___  _ __ | __ )  ___ | |_ \n'
  printf '  / _ \\| | | | __| `_ \\ / _ \\| `__||  _ \\ / _ \\| __|\n'
  printf ' / ___ \\ |_| | |_| | | | (_) | |   | |_) | (_) | |_ \n'
  printf '/_/   \\_\\__,_|\\__|_| |_|\\___/|_|   |____/ \\___/ \\__|\n'
  printf '\033[0m'
  printf '                 \033[2mby Author C\033[0m\n\n'
  printf '\033[0;36mGitHub:\033[0m https://github.com/VadymYem/AuthorBot\n'
  printf '\033[0;36mWeb:\033[0m    https://authorche.top\n\n'
}

step() { printf '\033[0;96m%s\033[0m\n' "$1"; }
ok() { printf '\033[0;32m%s\033[0m\n' "$1"; }
fail() {
  printf '\033[1;31m%s\033[0m\n' "$1" >&2
  [ -f "$LOG_FILE" ] && tail -n 120 "$LOG_FILE" >&2 || true
  exit "${2:-1}"
}
run() { "$@" >>"$LOG_FILE" 2>&1; }

banner_bootstrap
: >"$LOG_FILE"
step "Installing base packages..."
run pkg update -y
run pkg install -y build-essential ffmpeg git libcairo libffi libjpeg-turbo libwebp ncurses-utils openssl python
ok "Base packages ready."

step "Preparing source code..."
if [ -d "$APP_DIR/.git" ]; then
  run git -C "$APP_DIR" remote set-url origin "$REPO_URL"
  run git -C "$APP_DIR" fetch --prune origin
  BRANCH="$(git -C "$APP_DIR" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
  [ -n "$BRANCH" ] || BRANCH="main"
  run git -C "$APP_DIR" reset --hard "origin/$BRANCH"
  cd "$APP_DIR"
  ok "Existing AuthorBot updated; local sessions and database were preserved."
elif [ -e "$APP_DIR" ]; then
  fail "$APP_DIR already exists but is not a Git repository. Move it aside before installation." 3
else
  run git clone --depth=1 "$REPO_URL" "$APP_DIR" || fail "Source code download failed." 3
  cd "$APP_DIR"
  ok "Source code downloaded."
fi
[ -f assets/download.txt ] && while IFS= read -r line; do printf '%b\n' "$line"; done < assets/download.txt || true

step "Creating isolated Python environment..."
python -m venv .venv >>"$LOG_FILE" 2>&1 || fail "Could not create virtual environment." 4
VPY="$APP_DIR/.venv/bin/python"
run "$VPY" -m pip install --upgrade pip setuptools wheel

step "Installing Pillow and Python requirements..."
export CFLAGS="-I${PREFIX}/include/"
if [ "$(uname -m)" = "aarch64" ]; then
  export LDFLAGS="-L/system/lib64/ -L${PREFIX}/lib"
else
  export LDFLAGS="-L/system/lib/ -L${PREFIX}/lib"
fi
run "$VPY" -m pip install --upgrade Pillow --no-cache-dir
run "$VPY" -m pip install --upgrade -r requirements.txt --no-cache-dir --disable-pip-version-check || fail "Requirements installation failed." 5
if [ -f optional_requirements.txt ]; then
  run "$VPY" -m pip install --upgrade -r optional_requirements.txt --no-cache-dir --disable-pip-version-check || true
fi
ok "Python environment ready."

step "Running AuthorBot self-check..."
run "$VPY" scripts/selfcheck.py || fail "AuthorBot self-check failed." 6
ok "Self-check passed."
touch .setup_complete

if [ -z "${NO_AUTOSTART:-}" ]; then
  step "Configuring Termux autostart..."
  : >"$PREFIX/etc/motd"
  touch "$PROFILE"
  if ! grep -Fq "$MARKER" "$PROFILE"; then
    cat >>"$PROFILE" <<'PROFILE_BLOCK'

# >>> AuthorBot autostart >>>
if [ -x "$HOME/AuthorBot/.venv/bin/python" ]; then
  clear
  [ -x "$HOME/AuthorBot/banner.sh" ] && "$HOME/AuthorBot/banner.sh"
  cd "$HOME/AuthorBot" || return
  exec "$HOME/AuthorBot/.venv/bin/python" -m acbot
fi
# <<< AuthorBot autostart <<<
PROFILE_BLOCK
  fi
  ok "Autostart enabled without overwriting existing shell profile."
fi

printf '\n\033[1;32mAuthorBot is starting...\033[0m\n'
exec "$VPY" -m acbot
