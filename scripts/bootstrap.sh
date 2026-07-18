#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
  echo "Fredo needs uv. In Codex, ask it to install the current Astral uv release, then rerun this script." >&2
  exit 1
fi

uv sync --frozen --extra dev
if ! uv run fredo doctor --json; then
  echo "Dependencies are installed. Run 'uv run fredo configure', then rerun doctor." >&2
fi
