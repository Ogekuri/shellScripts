#!/bin/bash
# VERSION: 0.18.0
# AUTHORS: Ogekuri
# Launcher script for shellscripts CLI via Astral UV

# @brief Normalize a path for cross-platform comparison.
# @details Uses cygpath when available (Git Bash/MSYS) and falls back to
#   canonical directory resolution via cd/pwd -P.
# @param $1 Raw path to normalize.
# @return Prints the normalized path to stdout.
normalize_path() {
    local raw_path="$1"
    local normalized_path=""

    if command -v cygpath >/dev/null 2>&1; then
        normalized_path=$(cygpath -u "${raw_path}" 2>/dev/null)
        if [ -n "${normalized_path}" ]; then
            printf '%s\n' "${normalized_path}"
            return 0
        fi
    fi

    normalized_path=$(CDPATH= cd -- "${raw_path}" 2>/dev/null && pwd -P)
    if [ -n "${normalized_path}" ]; then
        printf '%s\n' "${normalized_path}"
        return 0
    fi

    printf '%s\n' "${raw_path}"
}

SCRIPT_PATH=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd -P)
BASE_DIR=$(CDPATH= cd -- "${SCRIPT_PATH}/.." 2>/dev/null && pwd -P)

PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Unable to determine project root from launcher path."
    exit 1
fi

PROJECT_ROOT=$(normalize_path "${PROJECT_ROOT}")
BASE_DIR=$(normalize_path "${BASE_DIR}")

if [ "${PROJECT_ROOT}" != "${BASE_DIR}" ]; then
    echo "ERROR: Launcher base directory mismatch with git root."
    echo "git root: ${PROJECT_ROOT}"
    echo "launcher base: ${BASE_DIR}"
    exit 1
fi

exec uv run --project "${BASE_DIR}" python -m shell_scripts "$@"
