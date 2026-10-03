#!/bin/bash
# Runs inside the dedicated Debian Bookworm PRoot guest, never in native Termux.
set -euo pipefail

APP_DIR=/opt/authorbot
VPY="$APP_DIR/.venv-proot/bin/python"
cd "$APP_DIR"

case "${1:-}" in
  install)
    # Refuse a reused container with a different distro instead of altering it.
    . /etc/os-release
    if [ "${VERSION_CODENAME:-}" != bookworm ]; then
      printf 'Потрібен Debian Bookworm; отримано %s.\n' "${PRETTY_NAME:-unknown}" >&2
      exit 3
    fi
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
      ca-certificates git ffmpeg build-essential pkg-config \
      python3.11 python3.11-venv python3.11-dev \
      libcairo2-dev libffi-dev libjpeg-dev libwebp-dev zlib1g-dev
    python3.11 -m venv "$APP_DIR/.venv-proot"
    "$VPY" -m pip install --upgrade pip setuptools wheel
    "$VPY" -m pip install -r requirements.txt
    "$VPY" -m pip install -r optional_requirements.txt
    "$VPY" -m pip check
    "$VPY" scripts/selfcheck.py
    "$VPY" scripts/runtimecheck.py
    "$VPY" -m acbot --help >/dev/null
    touch .setup_complete
    ;;
  run)
    shift
    if [ ! -x "$VPY" ] || [ ! -f .setup_complete ]; then
      printf 'Спочатку виконай bash termux.sh у Termux.\n' >&2
      exit 4
    fi
    export AUTHORBOT_TERMUX=1
    export VIRTUAL_ENV="$APP_DIR/.venv-proot"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
    # PRoot's guest root is mapped to the ordinary Android user, without root privileges.
    exec "$VPY" -m acbot --root --data-root "$APP_DIR" "$@"
    ;;
  *)
    printf 'Використання: termux-runtime.sh install|run\n' >&2
    exit 2
    ;;
esac
