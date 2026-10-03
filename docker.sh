#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${AUTHORBOT_REPO_URL:-https://github.com/VadymYem/AuthorBot.git}"
APP_DIR="${AUTHORBOT_DIR:-$HOME/AuthorBot}"
EXTERNAL_PORT="${EXTERNAL_PORT:-8085}"
BIND_ADDRESS="${BIND_ADDRESS:-127.0.0.1}"

info() { printf '\033[0;36m%s\033[0m\n' "$1"; }
ok() { printf '\033[0;32m%s\033[0m\n' "$1"; }
fail() { printf '\033[1;31m%s\033[0m\n' "$1" >&2; exit 1; }

command -v git >/dev/null 2>&1 || fail "git is required."
command -v docker >/dev/null 2>&1 || fail "Docker Engine is required. Install Docker from https://docs.docker.com/engine/install/"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 plugin is required."

if [ -d "$APP_DIR/.git" ]; then
  info "Updating AuthorBot checkout..."
  git -C "$APP_DIR" fetch --prune origin
  git -C "$APP_DIR" reset --hard origin/main
elif [ -e "$APP_DIR" ]; then
  fail "$APP_DIR exists but is not a Git repository."
else
  info "Cloning AuthorBot..."
  git clone --depth=1 "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [ ! -f .env ]; then
  if command -v python3 >/dev/null 2>&1; then
    PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  else
    PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
  fi

  umask 077
  cat > .env <<ENV
EXTERNAL_PORT=$EXTERNAL_PORT
BIND_ADDRESS=$BIND_ADDRESS
AUTHORBOT_WEB_USER=authorbot
AUTHORBOT_WEB_PASSWORD=$PASSWORD
ENV
  ok "Created private .env with a random web password."
else
  ok "Existing .env preserved."
fi

info "Building and starting AuthorBot..."
docker compose up -d --build

USER_NAME="$(grep '^AUTHORBOT_WEB_USER=' .env | cut -d= -f2- || true)"
PASSWORD="$(grep '^AUTHORBOT_WEB_PASSWORD=' .env | cut -d= -f2- || true)"
PORT="$(grep '^EXTERNAL_PORT=' .env | cut -d= -f2- || true)"
BIND="$(grep '^BIND_ADDRESS=' .env | cut -d= -f2- || true)"

printf '\n\033[1;32mAuthorBot container is running.\033[0m\n'
printf 'Web: http://%s:%s\n' "${BIND:-127.0.0.1}" "${PORT:-8085}"
printf 'User: %s\n' "${USER_NAME:-authorbot}"
printf 'Password: %s\n' "$PASSWORD"
printf '\nLogs: docker compose logs -f authorbot\n'
