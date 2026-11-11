#!/bin/bash
# VERSION: 0.26.0
# AUTHORS: Ogekuri
# Distribution package build pipeline for shellScripts.

# @file scripts/build.sh
# @brief Build and organize distribution release artifacts into dist/.
# @details Resolves the Git repository root from the script location,
#   validates toolchain availability (preferring `uv build` when `uv` is
#   executable and falling back to `.venv/bin/python3 -m build` or
#   `python3 -m build`), safely cleans stale generated distribution
#   archives (`*.tar.gz`, `*.whl`, `*.zip`, `*.egg`) under `dist/` while
#   preserving versioned or non-generated files, compiles the project,
#   verifies that `dist/` contains valid non-empty sdist and wheel packages,
#   and outputs a summary of generated deliverables. Exits with code 0 on
#   success and non-zero on any failure.
# @satisfies DES-040, DES-041, REQ-134, REQ-135

set -Eeuo pipefail

SCRIPT_PATH=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)
BASE_DIR=$(CDPATH= cd -- "${SCRIPT_PATH}/.." 2>/dev/null && pwd -P)

PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "${PROJECT_ROOT}" ]; then
    printf 'ERROR: Unable to determine project root from build script path.\n' >&2
    exit 1
fi

cd -- "${PROJECT_ROOT}" || exit 1

# @brief Safely remove stale generated build and packaging artifacts.
# @details Removes stale `.tar.gz`, `.whl`, `.zip`, and `.egg` files inside
#   `dist/` as well as intermediate `build` and `src/shellscripts.egg-info`
#   trees while preserving any non-generated or versioned files inside
#   `dist/`. Creates `dist/` if it does not already exist.
# @return {None} Modifies local filesystem.
# @satisfies DES-041, REQ-134
clean_stale_artifacts() {
    printf '==> Preparing dist/ directory and cleaning stale artifacts\n'
    mkdir -p dist
    rm -f -- dist/*.tar.gz dist/*.whl dist/*.zip dist/*.egg 2>/dev/null || true
    rm -rf -- build src/shellscripts.egg-info 2>/dev/null || true
}

# @brief Resolve and validate the build command from available toolchains.
# @details Evaluates `uv`, `.venv/bin/python3 -m build`, and `python3 -m build`
#   in order of preference. Sets BUILD_CMD to the selected command vector.
# @return {int} 0 when a supported toolchain is available; 1 otherwise.
# @satisfies REQ-134
resolve_build_tool() {
    if command -v uv >/dev/null 2>&1; then
        BUILD_TOOL="uv"
        BUILD_CMD=(uv build)
        return 0
    elif [ -x ".venv/bin/python3" ] && .venv/bin/python3 -m build --version >/dev/null 2>&1; then
        BUILD_TOOL=".venv python3 -m build"
        BUILD_CMD=(.venv/bin/python3 -m build)
        return 0
    elif python3 -m build --version >/dev/null 2>&1; then
        BUILD_TOOL="python3 -m build"
        BUILD_CMD=(python3 -m build)
        return 0
    else
        printf 'ERROR: No supported build tool found. Install uv or python3-build.\n' >&2
        return 1
    fi
}

# @brief Execute distribution package compilation.
# @details Invokes the resolved build tool to generate sdist and wheel packages
#   under the project `dist/` directory.
# @return Propagates the build tool exit code.
# @satisfies DES-040, DES-041, REQ-134
build_distributions() {
    printf '==> Building distribution packages using %s\n' "${BUILD_TOOL}"
    "${BUILD_CMD[@]}"
}

# @brief Verify that dist/ contains valid sdist and wheel release artifacts.
# @details Checks for presence and non-zero byte size of at least one
#   `dist/*.tar.gz` and at least one `dist/*.whl` file.
# @return {int} 0 on successful validation; 1 otherwise.
# @satisfies REQ-135
verify_artifacts() {
    local sdist_count=0
    local wheel_count=0

    for f in dist/*.tar.gz; do
        if [ -f "${f}" ] && [ -s "${f}" ]; then
            sdist_count=$((sdist_count + 1))
        fi
    done

    for f in dist/*.whl; do
        if [ -f "${f}" ] && [ -s "${f}" ]; then
            wheel_count=$((wheel_count + 1))
        fi
    done

    if [ "${sdist_count}" -eq 0 ]; then
        printf 'ERROR: Missing or empty sdist artifact (.tar.gz) in dist/.\n' >&2
        return 1
    fi

    if [ "${wheel_count}" -eq 0 ]; then
        printf 'ERROR: Missing or empty wheel artifact (.whl) in dist/.\n' >&2
        return 1
    fi

    return 0
}

# @brief Print formatted summary of generated release deliverables.
# @details Iterates all files in `dist/` and prints their paths and sizes.
# @return {None} Writes summary to stdout.
# @satisfies REQ-135
print_summary() {
    printf '\n========================================\n'
    printf 'BUILD SUMMARY: Artifacts generated in dist/\n'
    printf '========================================\n'
    for f in dist/*; do
        if [ -f "${f}" ]; then
            local size
            size=$(ls -lh "${f}" | awk '{print $5}')
            printf '  - %s (%s)\n' "${f}" "${size}"
        fi
    done
    printf '========================================\n'
    printf 'Build PASSED: all artifacts generated in dist/.\n'
}

clean_stale_artifacts
resolve_build_tool
build_distributions
verify_artifacts
print_summary

exit 0
