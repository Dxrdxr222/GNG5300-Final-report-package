#!/usr/bin/env bash

set -u

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

if [ -d ".venv-pi" ]; then
    # shellcheck disable=SC1091
    source ".venv-pi/bin/activate"
    PYTHON_BIN="python"
else
    PYTHON_BIN="python3"
fi

echo "Starting Visual Guide Robot from: $PROJECT_DIR"
echo "Python: $($PYTHON_BIN --version 2>&1)"
echo ""

exec "$PYTHON_BIN" pi_visual_guide.py
