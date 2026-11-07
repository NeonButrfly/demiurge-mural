#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  ./setup_mac.sh
fi

QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
