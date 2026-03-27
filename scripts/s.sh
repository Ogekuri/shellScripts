#!/bin/bash
# VERSION: 0.5.0
# AUTHORS: Ogekuri
# Launcher script for shellscripts CLI via Astral UV

FULL_PATH=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "$FULL_PATH")
BASE_DIR=$(dirname "$SCRIPT_PATH")

PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Unable to determine project root from launcher path."
    exit 1
fi

if [ "${PROJECT_ROOT}" != "${BASE_DIR}" ]; then
    echo "ERROR: Launcher base directory mismatch with git root."
    echo "git root: ${PROJECT_ROOT}"
    echo "launcher base: ${BASE_DIR}"
    exit 1
fi

exec uv run --project "${BASE_DIR}" python -m shell_scripts "$@"
