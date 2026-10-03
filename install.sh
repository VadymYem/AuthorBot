#!/usr/bin/env bash
set -euo pipefail

APP_NAME="AuthorBot"
MODULE_NAME="acbot"
REPO_URL="${AUTHORBOT_REPO_URL:-https://github.com/VadymYem/AuthorBot.git}"
VENV_DIR="${AUTHORBOT_VENV_DIR:-.venv}"
LOG_FILE="${AUTHORBOT_INSTALL_LOG:-$PWD/authorbot-install.log}"

info() { printf '\033[0;36m%s\033[0m\n' "$1"; }
ok() { printf '\033[0;32m%s\033[0m\n' "$1"; }
fail() {
  printf '\033[1;31m%s\033[0m\n' "$1" >&2
  [ -f "$LOG_FILE" ] && tail -n 120 "$LOG_FILE" >&2 || true
  exit "${2:-1}"
}
run() { "$@" >>"$LOG_FILE" 2>&1; }

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then printf 'python3';
  elif command -v python >/dev/null 2>&1; then printf 'python';
  else fail "Python is not installed." 2; fi
}

install_system_packages() {
  info "Installing system packages..."
  if [[ "${OSTYPE:-}" == linux-android* ]]; then
    run pkg update -y
    run pkg install -y build-essential ffmpeg git libcairo libffi libjpeg-turbo libwebp ncurses-utils openssl python
  elif command -v apt-get >/dev/null 2>&1; then
    local SUDO=()
    if [ "$(id -u)" -ne 0 ]; then
      command -v sudo >/dev/null 2>&1 || fail "Root privileges or sudo are required." 2
      SUDO=(sudo)
    fi
    run "${SUDO[@]}" apt-get update
    run "${SUDO[@]}" apt-get install -y build-essential ffmpeg git imagemagick libcairo2 libffi-dev libjpeg-dev libopenjp2-7 libtiff-dev libwebp-dev libz-dev python3 python3-dev python3-pip python3-venv
  elif command -v pacman >/dev/null 2>&1; then
    local SUDO=(); [ "$(id -u)" -eq 0 ] || SUDO=(sudo)
    run "${SUDO[@]}" pacman -Sy --needed --noconfirm base-devel ffmpeg git imagemagick python python-pip
  elif command -v brew >/dev/null 2>&1; then
    run brew install git jpeg webp python
  else
    info "Unknown package manager: system packages were not changed."
  fi
}

prepare_repo() {
  if [ -f "requirements.txt" ] && [ -d "$MODULE_NAME" ]; then
    return
  fi

  if [ -d "$APP_NAME/.git" ]; then
    info "Updating existing AuthorBot checkout..."
    run git -C "$APP_NAME" remote set-url origin "$REPO_URL"
    run git -C "$APP_NAME" fetch --prune origin
    local branch
    branch="$(git -C "$APP_NAME" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
    [ -n "$branch" ] || branch="main"
    run git -C "$APP_NAME" reset --hard "origin/$branch"
    cd "$APP_NAME"
    return
  fi

  if [ -e "$APP_NAME" ]; then
    fail "$APP_NAME already exists but is not a Git repository. Move it aside before installation." 3
  fi

  info "Downloading AuthorBot..."
  run git clone --depth=1 "$REPO_URL" "$APP_NAME" || fail "Repository clone failed." 3
  cd "$APP_NAME"
}

check_python() {
  "$1" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("AuthorBot requires Python 3.10+")
print(f"Python {sys.version.split()[0]}")
PY
}

install_python_packages() {
  local py="$1"
  info "Creating isolated Python environment..."
  run "$py" -m venv "$VENV_DIR" || fail "Virtual environment creation failed." 4
  local vpy="$VENV_DIR/bin/python"
  run "$vpy" -m pip install --upgrade pip setuptools wheel
  run "$vpy" -m pip install --upgrade -r requirements.txt --disable-pip-version-check || fail "Python requirements installation failed." 4
  if [ -f optional_requirements.txt ]; then
    run "$vpy" -m pip install --upgrade -r optional_requirements.txt --disable-pip-version-check || true
  fi
  run "$vpy" -m pip check || fail "Python dependency conflicts detected." 4
}

: >"$LOG_FILE"
clear 2>/dev/null || true
printf '\033[1;35mAuthor Bot\033[0m  \033[2mby AuthorChe\033[0m\n'
printf '\033[0;36mGitHub:\033[0m https://github.com/VadymYem/AuthorBot\n'
printf '\033[0;36mWeb:\033[0m    https://authorche.top\n\n'

install_system_packages
PYTHON="$(python_cmd)"
check_python "$PYTHON"
prepare_repo
[ -f assets/download.txt ] && while IFS= read -r line; do printf '%b\n' "$line"; done < assets/download.txt || true
install_python_packages "$PYTHON"
info "Running AuthorBot self-check..."
run "$VENV_DIR/bin/python" scripts/selfcheck.py || fail "AuthorBot self-check failed." 6
run "$VENV_DIR/bin/python" scripts/runtimecheck.py || fail "AuthorBot runtime checks failed." 6
run "$VENV_DIR/bin/python" scripts/startupcheck.py || fail "AuthorBot startup checks failed." 6
run "$VENV_DIR/bin/python" -c 'from acbot.runtime_state import mark_dependencies_ready; mark_dependencies_ready()'
touch .setup_complete
ok "AuthorBot installation complete."
exec "$VENV_DIR/bin/python" -m "$MODULE_NAME" "$@"
