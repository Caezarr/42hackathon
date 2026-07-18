#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
LOCAL_BIN="$PROJECT_DIR/.fredo-tools/bin"

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  if command -v brew >/dev/null 2>&1; then
    brew install uv
    return
  fi
  if command -v curl >/dev/null 2>&1; then
    mkdir -p "$LOCAL_BIN"
    curl -LsSf https://astral.sh/uv/0.10.9/install.sh \
      | UV_INSTALL_DIR="$LOCAL_BIN" sh
    PATH="$LOCAL_BIN:$PATH"
    export PATH
    return
  fi
  echo "Fredo cannot install uv automatically: install uv or Homebrew first." >&2
  exit 1
}

ensure_cloudflared() {
  if command -v cloudflared >/dev/null 2>&1; then
    return
  fi
  if command -v brew >/dev/null 2>&1; then
    brew install cloudflared
    return
  fi
  echo "Fredo needs cloudflared for Twilio callbacks; install Homebrew or cloudflared." >&2
  exit 1
}

ensure_uv
ensure_cloudflared

if ! command -v uv >/dev/null 2>&1; then
  echo "Fredo could not put uv on PATH after installation." >&2
  exit 1
fi

uv sync --frozen --extra dev
if ! uv run fredo doctor --json; then
  echo "Dependencies are installed. Run 'uv run fredo configure', then rerun doctor." >&2
fi
