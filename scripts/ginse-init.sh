#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' 'Usage: scripts/ginse-init.sh /absolute/path/to/verified-ginse-runner https://host.example/run' >&2
  exit 2
fi

GINSE_RUNNER="$1"
RUN_URL="$2"

case "$GINSE_RUNNER" in
  /*) ;;
  *)
    printf '%s\n' 'GINSE runner path must be absolute.' >&2
    exit 2
    ;;
esac

if [ ! -f "$GINSE_RUNNER" ] || [ ! -x "$GINSE_RUNNER" ]; then
  printf '%s\n' 'GINSE runner must be the executable, SHA-verified file from the official bootstrap.' >&2
  exit 2
fi

case "$RUN_URL" in
  https://?*/run) ;;
  *)
    printf '%s\n' 'Run URL must be an HTTPS URL ending in /run.' >&2
    exit 2
    ;;
esac

RUN_AUTHORITY=${RUN_URL#https://}
RUN_AUTHORITY=${RUN_AUTHORITY%/run}
case "$RUN_AUTHORITY" in
  ''|*/*)
    printf '%s\n' 'Run URL must be the provider origin followed by /run.' >&2
    exit 2
    ;;
esac

case "$RUN_URL" in
  *[[:space:]]*|*'@'*|*'?'*|*'#'*)
    printf '%s\n' 'Run URL must not contain credentials, whitespace, a query, or a fragment.' >&2
    exit 2
    ;;
esac

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

exec "$GINSE_RUNNER" apps init fredo-demo \
  --display-name 'Fredo — 42hackathon' \
  --description 'Prepare a compatible hosted Fredo voice demo session.' \
  --price-cents 42 \
  --run-url "$RUN_URL" \
  --input-schema "$PROJECT_DIR/schemas/ginse-input.schema.json" \
  --output-schema "$PROJECT_DIR/schemas/ginse-output.schema.json" \
  --input-label 'Mac demo profile' \
  --input-icon code \
  --action-label 'Prepare Fredo demo' \
  --output-label 'Fredo demo session' \
  --output-icon audio \
  --example "$PROJECT_DIR/schemas/ginse-example-input.json" \
  --json
