#!/bin/bash
# VERSION: 0.26.0
# AUTHORS: Ogekuri
# Distribution package build pipeline for shellScripts.

# @file scripts/build.sh
# @brief Build every distribution deliverable and keep it available in dist/.
# @details Resolves the Git repository root from the script location, validates
#   Python 3.11 or newer plus one supported build tool (`uv build` preferred,
#   `python3 -m build` fallback), removes stale generated archives and
#   intermediate build trees without touching tracked or non-generated
#   `dist/` entries, builds sdist and wheel packages into `dist/`, validates
#   that both archive classes are non-empty and readable, and prints one
#   summary listing every deliverable left in `dist/`. Terminates with a
#   non-zero status on any mandatory failure and never deletes artifacts it
#   has just produced.
# @satisfies DES-040, DES-041, DES-046, REQ-134, REQ-135, REQ-141

set -Eeuo pipefail
shopt -s nullglob

DIST_DIR="dist"
PYTHON_BIN=""
BUILD_TOOL=""
BUILD_CMD=()

# @brief Print one labeled phase header.
# @details Centralizes the phase-header format so build logs are parser-stable
#   and every mandatory phase is clearly delimited. Time complexity O(1).
# @param $1 Phase title text.
# @return {None} Writes one stdout line.
# @satisfies REQ-142
log_phase() {
    printf '\n==> %s\n' "$1"
}

# @brief Print one diagnostic error line to stderr.
# @details Keeps every failure message on the error stream with a fixed
#   `ERROR: ` prefix so callers and CI logs can classify failures. Time
#   complexity O(1).
# @param $1 Diagnostic text.
# @return {None} Writes one stderr line.
# @satisfies REQ-134
log_error() {
    printf 'ERROR: %s\n' "$1" >&2
}

# @brief Resolve the repository root and change into it.
# @details Derives the script directory from `BASH_SOURCE[0]`, resolves the
#   parent project directory, asks Git for the canonical working-tree root,
#   and changes the current directory to that root so the script works from
#   any invocation directory and with paths containing spaces. Time
#   complexity O(1) excluding Git startup latency.
# @return {int} 0 on success; 1 when the Git root cannot be resolved.
# @satisfies DES-040, REQ-134
resolve_project_root() {
    local script_path
    local base_dir
    local project_root

    script_path=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P) || return 1
    base_dir=$(CDPATH= cd -- "${script_path}/.." 2>/dev/null && pwd -P) || return 1
    project_root=$(git -C "${base_dir}" rev-parse --show-toplevel 2>/dev/null) || return 1
    if [ -z "${project_root}" ]; then
        return 1
    fi
    cd -- "${project_root}"
}

# @brief Resolve the Python interpreter used for validation steps.
# @details Prefers the project virtual environment interpreter when it is
#   executable and falls back to `python3`, matching the repository test
#   toolchain convention. Time complexity O(1).
# @return {None} Updates the global PYTHON_BIN value.
# @satisfies DES-040, REQ-134
resolve_python_interpreter() {
    if [ -x ".venv/bin/python3" ]; then
        PYTHON_BIN=".venv/bin/python3"
    else
        PYTHON_BIN="python3"
    fi
}

# @brief Validate the Python runtime and select one build tool.
# @details Requires Python 3.11 or newer, then selects `uv build` when `uv`
#   is executable or `<python> -m build` when the `build` module is
#   importable. Time complexity O(1) excluding interpreter startup.
# @return {int} 0 when both validations succeed; 1 otherwise.
# @satisfies DES-040, REQ-134
resolve_build_tool() {
    if ! "${PYTHON_BIN}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
        log_error "Python 3.11 or newer is required (resolved interpreter: ${PYTHON_BIN})."
        return 1
    fi

    if command -v uv >/dev/null 2>&1; then
        BUILD_TOOL="uv build"
        BUILD_CMD=(uv build)
        return 0
    fi

    if "${PYTHON_BIN}" -c 'import build' >/dev/null 2>&1; then
        BUILD_TOOL="${PYTHON_BIN} -m build"
        BUILD_CMD=("${PYTHON_BIN}" -m build)
        return 0
    fi

    log_error "No supported build tool found; install uv or the Python build module."
    return 1
}

# @brief Abort when tracked files live under removable generated paths.
# @details Queries Git for tracked entries under the intermediate build trees
#   that the pipeline may remove. Any tracked entry makes deletion unsafe, so
#   the function fails before destructive operations. Time complexity O(n)
#   over tracked path count.
# @return {int} 0 when no tracked entry exists; 1 otherwise.
# @satisfies DES-041, REQ-141
assert_no_tracked_intermediates() {
    local tracked

    tracked=$(git ls-files -- build src/shellscripts.egg-info) || return 1
    if [ -n "${tracked}" ]; then
        log_error "Tracked files exist under removable build paths:"
        printf '%s\n' "${tracked}" >&2
        return 1
    fi
    return 0
}

# @brief Remove stale generated archives and intermediate build trees.
# @details Creates `dist/` when absent, iterates every top-level generated
#   archive pattern, refuses to delete any tracked archive, removes the
#   untracked generated archives, and deletes the `build` and
#   `src/shellscripts.egg-info` intermediate trees. Non-generated or tracked
#   `dist/` entries are preserved. Time complexity O(n) over removed entries.
# @return {int} 0 on success; 1 when a tracked artifact or removal blocks.
# @satisfies DES-041, REQ-141
clean_stale_artifacts() {
    local artifact

    assert_no_tracked_intermediates || return 1
    mkdir -p -- "${DIST_DIR}" || return 1

    for artifact in "${DIST_DIR}"/*.tar.gz "${DIST_DIR}"/*.whl "${DIST_DIR}"/*.zip "${DIST_DIR}"/*.egg; do
        if git ls-files --error-unmatch -- "${artifact}" >/dev/null 2>&1; then
            log_error "Refusing to delete tracked release artifact: ${artifact}"
            return 1
        fi
        rm -f -- "${artifact}" || return 1
    done

    remove_generated_dist_metadata || return 1

    if [ -d "build" ]; then
        rm -rf -- "build" || return 1
    fi
    if [ -d "src/shellscripts.egg-info" ]; then
        rm -rf -- "src/shellscripts.egg-info" || return 1
    fi
    return 0
}

# @brief Remove build-tool metadata that would hide non-generated dist files.
# @details `uv build` writes `dist/.gitignore` containing a blanket `*` rule,
#   which would hide every non-generated file placed in `dist/`. The metadata
#   file is generated output, so it is removed to keep the repository root
#   `.gitignore` inverse rules authoritative; a tracked metadata file is never
#   deleted. Time complexity O(1).
# @return {int} 0 on success; 1 when a tracked metadata file blocks removal.
# @satisfies DES-041, REQ-141
remove_generated_dist_metadata() {
    if [ ! -e "${DIST_DIR}/.gitignore" ] && [ ! -L "${DIST_DIR}/.gitignore" ]; then
        return 0
    fi
    if git ls-files --error-unmatch -- "${DIST_DIR}/.gitignore" >/dev/null 2>&1; then
        log_error "Refusing to delete tracked release metadata: ${DIST_DIR}/.gitignore"
        return 1
    fi
    rm -f -- "${DIST_DIR}/.gitignore" || return 1
    return 0
}

# @brief Execute the selected distribution build tool.
# @details Runs the resolved build command vector from the repository root so
#   sdist and wheel packages are written into `dist/`. Time complexity O(n)
#   over project size plus toolchain latency.
# @return Propagates the build tool exit status.
# @satisfies DES-040, REQ-134
build_distributions() {
    printf 'Build tool: %s\n' "${BUILD_TOOL}"
    "${BUILD_CMD[@]}"
}

# @brief Execute the build tool and normalize generated dist metadata.
# @details Delegates packaging to the selected build tool, then removes the
#   build-tool `dist/.gitignore` metadata so the repository root ignore rules
#   remain authoritative for non-generated files. Time complexity O(n) over
#   project size plus toolchain latency.
# @return {int} 0 when the build and metadata normalization succeed; 1
#   otherwise.
# @satisfies DES-040, REQ-134, REQ-141
run_distribution_build() {
    build_distributions || return 1
    remove_generated_dist_metadata || return 1
    return 0
}

# @brief Validate generated sdist and wheel deliverables.
# @details Requires at least one non-empty `.tar.gz` sdist and one non-empty
#   `.whl` wheel, then verifies archive readability with the Python standard
#   library (`tarfile` listing and `zipfile` CRC test). Time complexity O(n)
#   over archive contents.
# @return {int} 0 when every generated archive is valid; 1 otherwise.
# @satisfies DES-046, REQ-135
verify_artifacts() {
    local -a sdists=("${DIST_DIR}"/*.tar.gz)
    local -a wheels=("${DIST_DIR}"/*.whl)
    local artifact

    if [ "${#sdists[@]}" -eq 0 ]; then
        log_error "Missing sdist artifact (.tar.gz) in ${DIST_DIR}/."
        return 1
    fi
    if [ "${#wheels[@]}" -eq 0 ]; then
        log_error "Missing wheel artifact (.whl) in ${DIST_DIR}/."
        return 1
    fi

    for artifact in "${sdists[@]}"; do
        if [ ! -s "${artifact}" ]; then
            log_error "Empty sdist artifact: ${artifact}"
            return 1
        fi
        if ! "${PYTHON_BIN}" -m tarfile -l "${artifact}" >/dev/null; then
            log_error "Unreadable sdist artifact: ${artifact}"
            return 1
        fi
    done

    for artifact in "${wheels[@]}"; do
        if [ ! -s "${artifact}" ]; then
            log_error "Empty wheel artifact: ${artifact}"
            return 1
        fi
        if ! "${PYTHON_BIN}" -m zipfile -t "${artifact}" >/dev/null; then
            log_error "Unreadable wheel artifact: ${artifact}"
            return 1
        fi
    done

    printf 'Validated artifacts: %d sdist, %d wheel\n' "${#sdists[@]}" "${#wheels[@]}"
    return 0
}

# @brief Print the final deliverable summary.
# @details Iterates every file currently present in `dist/`, including
#   preserved non-generated entries, and prints its path and human-readable
#   size. Time complexity O(n) over `dist/` file count.
# @return {None} Writes summary lines to stdout.
# @satisfies DES-046, REQ-135
print_summary() {
    local artifact
    local size

    printf '\n========================================\n'
    printf 'BUILD SUMMARY: deliverables in %s/\n' "${DIST_DIR}"
    printf '========================================\n'
    for artifact in "${DIST_DIR}"/*; do
        if [ -f "${artifact}" ]; then
            size=$(du -h -- "${artifact}" | cut -f1)
            printf '  - %s (%s)\n' "${artifact}" "${size}"
        fi
    done
    printf '========================================\n'
    printf 'Build PASSED: distribution artifacts are available in %s/.\n' "${DIST_DIR}"
}

log_phase "Phase 1: Repository root and toolchain"
if ! resolve_project_root; then
    log_error "Unable to determine project root from build script path."
    exit 1
fi
resolve_python_interpreter
if ! resolve_build_tool; then
    exit 1
fi

log_phase "Phase 2: Stale artifact cleanup"
if ! clean_stale_artifacts; then
    exit 1
fi

log_phase "Phase 3: Distribution build"
if ! run_distribution_build; then
    log_error "Distribution build failed."
    exit 1
fi

log_phase "Phase 4: Artifact validation"
if ! verify_artifacts; then
    exit 1
fi

log_phase "Phase 5: Deliverable summary"
print_summary

exit 0
