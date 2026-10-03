#!/data/data/com.termux/files/usr/bin/bash
# Standalone entry point for a fresh Termux session.
set -euo pipefail

if ! command -v pkg >/dev/null || [ -z "${PREFIX:-}" ]; then
  printf 'Цей скрипт потрібно запускати у Termux.\n' >&2
  exit 2
fi

APP_DIR="${AUTHORBOT_APP_DIR:-$HOME/AuthorBot}"
REPO_URL=https://github.com/AuthorGramProject/AuthorBot.git

printf 'AuthorBot: автоматичне встановлення\n'
pkg update -y
pkg install -y git proot-distro

if [ -d "$APP_DIR/.git" ]; then
  printf '\nОновлюю AuthorBot…\n'
  # Fast-forward only: keep local files, sessions and intentional code edits.
  git -C "$APP_DIR" fetch origin main
  git -C "$APP_DIR" merge --ff-only origin/main
elif [ -e "$APP_DIR" ]; then
  printf '%s уже існує і не є Git-репозиторієм. Встановлення зупинено.\n' "$APP_DIR" >&2
  exit 3
else
  git clone --depth 1 --branch main "$REPO_URL" "$APP_DIR"
fi

exec bash "$APP_DIR/termux.sh" "$@"
