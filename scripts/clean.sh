#!/bin/bash
# VERSION: 0.26.0
# AUTHORS: Ogekuri
# Build-artifact cleanup for shellScripts.

# @file scripts/clean.sh
# @brief Remove every generated artifact produced by `scripts/build.sh`.
# @details Resolves the Git repository root from the script location, then
#   removes the intermediate `build/` and `src/shellscripts.egg-info/` trees
#   plus every untracked generated `dist` release archive. Tracked `dist/`
#   release deliverables and non-generated `dist` entries are preserved.
#   Tracked entries under the removable build trees abort cleanup. One
#   parser-stable `clean` evidence line is printed on success.
# @satisfies DES-055, REQ-147

set -Eeuo pipefail
shopt -s nullglob

DIST_DIR="dist"

# @brief Print one diagnostic error line to stderr.
# @details Keeps every failure message on the error stream with a fixed
#   `ERROR: ` prefix so callers and logs can classify failures. Time
#   complexity O(1).
# @param $1 Diagnostic text.
# @return {None} Writes one stderr line.
# @satisfies DES-055
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
# @satisfies DES-055, REQ-147
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

# @brief Remove the intermediate build trees, refusing tracked entries.
# @details Deletes the `build` and `src/shellscripts.egg-info` intermediate
#   trees produced by the packaging toolchain, refusing the operation when
#   any tracked file lives under them. Time complexity O(n) over removed
#   entries.
# @return {int} 0 on success; 1 when a tracked entry blocks removal or a
#   deletion fails.
# @satisfies DES-055, REQ-147
remove_intermediate_build_trees() {
    local path
    local tracked

    tracked=$(git ls-files -- build src/shellscripts.egg-info) || return 1
    if [ -n "${tracked}" ]; then
        log_error "Tracked files exist under removable build paths:"
        printf '%s\n' "${tracked}" >&2
        return 1
    fi

    for path in build src/shellscripts.egg-info; do
        if [ -e "${path}" ] || [ -L "${path}" ]; then
            rm -rf -- "${path}" || return 1
        fi
    done
    return 0
}

# @brief Remove untracked generated release archives from `dist`.
# @details Iterates top-level `dist` sdist, wheel, zip, and egg archives and
#   removes every archive that Git does not track. Tracked `dist/` release
#   deliverables and non-generated `dist` entries are preserved. Time
#   complexity O(n) over `dist` entry count.
# @return {int} 0 on success; 1 when a deletion fails.
# @satisfies DES-055, REQ-147
remove_untracked_dist_archives() {
    local artifact

    if [ ! -d "${DIST_DIR}" ]; then
        return 0
    fi
    for artifact in "${DIST_DIR}"/*.tar.gz "${DIST_DIR}"/*.whl "${DIST_DIR}"/*.zip "${DIST_DIR}"/*.egg; do
        if [ -n "$(git ls-files -- "${artifact}")" ]; then
            continue
        fi
        rm -f -- "${artifact}" || return 1
    done
    return 0
}

# @brief Execute the build-artifact cleanup and print one evidence line.
# @details Removes the intermediate build trees and the untracked generated
#   `dist` archives, then prints one parser-stable `clean` line listing the
#   removed artifact groups. Time complexity O(n) over removed entries.
# @return {int} 0 on success; 1 when a guard or deletion fails.
# @satisfies DES-055, REQ-147
clean_build_artifacts() {
    remove_intermediate_build_trees || return 1
    remove_untracked_dist_archives || return 1
    printf 'clean: build src/shellscripts.egg-info dist:untracked-archives\n'
    return 0
}

if ! resolve_project_root; then
    log_error "Unable to determine project root from clean script path."
    exit 1
fi

if ! clean_build_artifacts; then
    log_error "Build-artifact cleanup failed."
    exit 1
fi

exit 0
