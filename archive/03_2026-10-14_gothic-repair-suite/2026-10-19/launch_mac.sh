#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  ./setup_mac.sh
fi

exec .venv/bin/python -m gothic_repair.app \
  --source assets/current/Demiurge_Current_2048_2026-10-19.png
