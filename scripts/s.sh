#!/bin/bash
# -*- coding: utf-8 -*-
# VERSION: 0.0.0
# AUTHORS: Ogekuri

#/**
# * @brief Capture invocation timestamp for optional logging or tracing.
# * @details Single assignment; format `YYYY-MM-DD_HH-MM-SS` derived from system clock at startup.
# * @satisfies REQ-026
# */
now=$(date '+%Y-%m-%d_%H-%M-%S')

#/**
# * @brief Resolve absolute path of executing script.
# * @details Uses `readlink -f "$0"` to canonicalize all symlinks and relative components.
# *          Result is stored for directory and name extraction.
# * @satisfies REQ-026 REQ-030
# */
FULL_PATH=$(readlink -f "$0")

#/**
# * @brief Extract directory component of resolved script path.
# * @details Derived from FULL_PATH via `dirname`. Used as SRC_DIR base.
# * @satisfies REQ-026 REQ-030
# */
SCRIPT_PATH=$(dirname "$FULL_PATH")

#/**
# * @brief Extract filename component of resolved script path.
# * @details Derived from FULL_PATH via `basename`. Available for diagnostics.
# * @satisfies REQ-026
# */
SCRIPT_NAME=$(basename "$FULL_PATH")

#/**
# * @brief Extract base directory.
# * @details Derived from SCRIPT_PATH via `dirname`. Used as BASE_DIR base.
# */
BASE_DIR=$(dirname "$SCRIPT_PATH")

###############################################################################
## @brief Resolve project root from git repository.
## @details Uses `git -C "${BASE_DIR}" rev-parse --show-toplevel` to determine
##          canonical project root from launcher base directory.
##          Exits non-zero with explicit error when root detection fails.
## @satisfies REQ-034 REQ-007 DES-001
###############################################################################
PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Unable to determine project root from launcher path."
    exit 1
fi

###############################################################################
## @brief Validate launcher base directory against resolved git root.
## @details Prevents mixed-root execution when script path and git root differ.
##          Fails fast with explicit diagnostics to preserve deterministic runtime
##          environment resolution for uv project execution.
## @satisfies CTN-002
###############################################################################
if [ "${PROJECT_ROOT}" != "${BASE_DIR}" ]; then
    echo "ERROR: Launcher base directory mismatch with git root."
    echo "git root: ${PROJECT_ROOT}"
    echo "launcher base: ${BASE_DIR}"
    exit 1
fi

###############################################################################
## @brief Resolve Astral uv executable name.
## @details Stores canonical command token used for runtime delegation.
##          Launcher requires uv to create and manage execution environment.
## @satisfies CTN-002 CPT-005
###############################################################################
UV_TOOL="uv"

###############################################################################
## @brief Delegate CLI execution to Astral uv runtime.
## @details Executes `uv run --project <BASE_DIR> python -m shell_scripts` and
##          forwards all user CLI arguments unchanged. No `.venv` bootstrap,
##          activation, or pip installation logic is used.
## @satisfies CTN-002 CPT-005 CPT-002
###############################################################################
exec "${UV_TOOL}" run --project "${BASE_DIR}" python -m shell_scripts "$@"
