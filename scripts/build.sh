#!/bin/bash
# VERSION: 0.26.0
# AUTHORS: Ogekuri
# Distribution package build pipeline for shellScripts.

# @file scripts/build.sh
# @brief Build every distribution deliverable and keep it available in dist/.
# @details Resolves the Git repository root from the script location, validates
#   Python 3.11 or newer plus one supported build tool (`uv build` preferred,
#   `python3 -m build` fallback), resolves a deterministic SOURCE_DATE_EPOCH
#   from the tracked `.build-epoch` file,
#   removes every previous `dist/` archive of any version together with the
#   intermediate build trees while preserving non-generated `dist/` entries,
#   builds sdist and wheel packages into `dist/`, removes every intermediate
#   artifact produced by the build process, validates that both archive classes
#   are non-empty, readable, and member-compliant, and prints one summary
#   listing every deliverable left in `dist/`. Registers EXIT, INT, and TERM
#   traps so generated residue is removed on every termination path after the
#   project root is resolved. Emits one PASS or FAIL evidence line per phase
#   and terminates with a non-zero status on any mandatory failure.
# @satisfies DES-040, DES-041, DES-045, DES-046, DES-047, DES-052, DES-053,
#   DES-060, DES-061, DES-063, DES-065, REQ-134, REQ-135, REQ-141, REQ-145,
#   REQ-146, REQ-148, REQ-149, REQ-150, REQ-151, REQ-152

set -Eeuo pipefail
shopt -s nullglob

DIST_DIR="dist"
EPOCH_FILE=".build-epoch"
EPOCH_SOURCE=""
PYTHON_BIN=""
BUILD_TOOL=""
BUILD_CMD=()
PROJECT_ROOT_READY=0
CURRENT_PHASE="startup"
CLEANUP_DONE=0
SUMMARY_PRINTED=0

# @brief Print one labeled phase header.
# @details Centralizes the phase-header format so build logs are parser-stable
#   and every mandatory phase is clearly delimited. Time complexity O(1).
# @param $1 {str} Phase title text.
# @return {None} Writes one stdout line.
# @satisfies REQ-142
log_phase() {
    printf '\n==> %s\n' "$1"
}

# @brief Print one diagnostic error line to stderr.
# @details Keeps every failure message on the error stream with a fixed
#   `ERROR: ` prefix so callers and CI logs can classify failures. Time
#   complexity O(1).
# @param $1 {str} Diagnostic text.
# @return {None} Writes one stderr line.
# @satisfies REQ-134
log_error() {
    printf 'ERROR: %s\n' "$1" >&2
}

# @brief Start one phase and record it as the active phase.
# @details Prints the phase header and stores the title in `CURRENT_PHASE`
#   so the EXIT trap can name the failed phase in the final summary. Time
#   complexity O(1).
# @param $1 {str} Phase title text.
# @return {None} Writes one stdout line and updates `CURRENT_PHASE`.
# @satisfies DES-047, REQ-142
begin_phase() {
    CURRENT_PHASE="$1"
    log_phase "$1"
}

# @brief Emit one PASS evidence line for the active phase.
# @details Prints `PASS: <phase title>` to stdout. Called only after every
#   mandatory check of the phase succeeded. Time complexity O(1).
# @return {None} Writes one stdout line.
# @satisfies DES-047, REQ-142
pass_phase() {
    printf 'PASS: %s\n' "${CURRENT_PHASE}"
}

# @brief Emit one FAIL evidence line for the active phase and abort.
# @details Prints `FAIL: <phase title>` to stdout, the diagnostic to stderr
#   through `log_error`, and exits with status 1. The EXIT trap then performs
#   cleanup and prints the failure summary. Time complexity O(1).
# @param $1 {str} Diagnostic text.
# @return Does not return; exits the process with status 1.
# @satisfies DES-047, DES-045
fail_phase() {
    printf 'FAIL: %s\n' "${CURRENT_PHASE}"
    log_error "$1"
    exit 1
}

# @brief Convert an interrupt signal into a cleanup-eligible failure exit.
# @details Logs the received signal name and exits with the conventional
#   status so the EXIT trap removes generated build trees while the non-zero
#   status is preserved. Time complexity O(1).
# @param $1 {str} Signal name token (`INT` or `TERM`).
# @param $2 {int} Conventional exit status (130 for INT, 143 for TERM).
# @return Does not return; exits the process with status `$2`.
# @satisfies DES-045
on_signal() {
    log_error "Interrupted by $1 signal."
    exit "$2"
}

# @brief EXIT trap: remove generated build residue on every termination path.
# @details Captures the process status on entry and, once the project root is
#   resolved (`PROJECT_ROOT_READY=1`), removes every intermediate build artifact
#   through `clean_build_residue` so relative paths never resolve against the
#   invocation directory. A cleanup failure forces status 1 only when the status
#   was 0; a non-zero status is never overridden. Prints one `BUILD FAILED`
#   summary line naming the active phase when the status is non-zero. Idempotent
#   through `CLEANUP_DONE`. Time complexity O(n) over removed entries.
# @return Does not return; exits the process with the resolved status.
# @satisfies DES-045, DES-052, DES-061, REQ-141, REQ-148
on_exit() {
    local exit_code=$?
    trap - EXIT INT TERM

    if [ "${PROJECT_ROOT_READY}" -eq 1 ] && [ "${CLEANUP_DONE}" -eq 0 ]; then
        CLEANUP_DONE=1
        if ! clean_build_residue; then
            log_error "Generated build-tree cleanup failed."
            if [ "${exit_code}" -eq 0 ]; then
                exit_code=1
            fi
        fi
    fi

    if [ "${exit_code}" -ne 0 ] && [ "${SUMMARY_PRINTED}" -eq 0 ]; then
        SUMMARY_PRINTED=1
        printf '\nBUILD FAILED during: %s (exit status %d)\n' \
            "${CURRENT_PHASE}" "${exit_code}"
    fi
    exit "${exit_code}"
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
# @note Build-backend constraints: `pyproject.toml` `[build-system].requires`
#   declares lower bounds only (`setuptools>=77.0.0`, `wheel>=0.41.0`,
#   `build>=1.0.0`). The backend version is therefore resolved at build time
#   by the selected tool. The generator version is recorded in the wheel
#   `WHEEL` metadata (`Generator:` line). Byte-identical rebuilds require the
#   same backend version; the deterministic SOURCE_DATE_EPOCH is exported by
#   `resolve_source_date_epoch` and honored by the backend and by
#   `strip_sdist_generated_members`.
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

# @brief Resolve the deterministic SOURCE_DATE_EPOCH for packaging.
# @details Honors an externally supplied SOURCE_DATE_EPOCH after validating it
#   as a non-negative decimal integer. When the variable is unset or empty,
#   reads the epoch from the version-controlled `.build-epoch` file so archive
#   timestamps depend on repository content instead of Git commit metadata, and
#   a clean tree rebuilt at the commit that contains the tracked `dist/`
#   archives yields byte-identical archives. Records the source token used by
#   `build_distributions` evidence output and exports the value so the build
#   backend and the sdist rewrite share one timestamp. Time complexity O(1)
#   excluding one file read.
# @pre Current directory equals the repository root.
# @post `SOURCE_DATE_EPOCH` is exported, matches `^[0-9]+$`, and `EPOCH_SOURCE`
#   is either `environment` or `.build-epoch`.
# @return {int} 0 on success; 1 when the supplied value or `.build-epoch`
#   content is missing or malformed.
# @satisfies DES-040, DES-063, REQ-134, REQ-149, REQ-150
resolve_source_date_epoch() {
    EPOCH_SOURCE="environment"
    if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
        EPOCH_SOURCE="${EPOCH_FILE}"
        if [ ! -f "${EPOCH_FILE}" ]; then
            log_error "Missing build epoch file: ${EPOCH_FILE}"
            return 1
        fi
        SOURCE_DATE_EPOCH=$(head -n 1 -- "${EPOCH_FILE}") || return 1
    fi
    case "${SOURCE_DATE_EPOCH}" in
        ''|*[!0-9]*)
            log_error "SOURCE_DATE_EPOCH must be a non-negative integer: ${SOURCE_DATE_EPOCH:-empty}"
            return 1
            ;;
    esac
    export SOURCE_DATE_EPOCH
    return 0
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

# @brief Remove every previous build archive and intermediate build tree.
# @details Creates `dist/` when absent, deletes every top-level sdist, wheel,
#   zip, and egg archive regardless of its version number and regardless of Git
#   tracking status, then removes the build-tool `dist/.gitignore` metadata and
#   the `build` and `src/shellscripts.egg-info` intermediate trees. Non-generated
#   `dist/` entries are preserved. Executed as the first data-mutating build
#   phase so a build always starts from an empty archive set; the same archive
#   set is removed by `scripts/pre-release-check.sh` before it delegates to this
#   script. Time complexity O(n) over removed entries.
# @return {int} 0 on success; 1 when the intermediate-tree guard or a removal blocks.
# @satisfies DES-041, DES-060, DES-065, REQ-141, REQ-152
clean_previous_builds() {
    local artifact

    assert_no_tracked_intermediates || return 1
    mkdir -p -- "${DIST_DIR}" || return 1

    for artifact in "${DIST_DIR}"/*.tar.gz "${DIST_DIR}"/*.whl "${DIST_DIR}"/*.zip "${DIST_DIR}"/*.egg; do
        rm -f -- "${artifact}" || return 1
    done

    remove_generated_dist_metadata || return 1

    remove_intermediate_build_trees || return 1
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

# @brief Remove intermediate build trees produced by the packaging backend.
# @details Refuses removal when tracked files exist under `build` or
#   `src/shellscripts.egg-info`, then deletes both directories when present.
#   Invoked before the build (stale trees), after packaging (generated
#   metadata residue), and from the EXIT trap `on_exit` on every termination
#   path. Idempotent: absent trees are skipped. Time complexity O(n) over
#   removed entries.
# @pre Current directory equals the repository root (`PROJECT_ROOT_READY=1`
#   when called from `on_exit`).
# @post `build/` and `src/shellscripts.egg-info/` are absent when no tracked
#   entry blocks removal.
# @return {int} 0 on success; 1 when a tracked entry or removal blocks.
# @satisfies DES-041, DES-052, DES-045, REQ-141
remove_intermediate_build_trees() {
    assert_no_tracked_intermediates || return 1
    if [ -d "build" ]; then
        rm -rf -- "build" || return 1
    fi
    if [ -d "src/shellscripts.egg-info" ]; then
        rm -rf -- "src/shellscripts.egg-info" || return 1
    fi
    return 0
}

# @brief Remove temporary packaging files left in `dist`.
# @details Deletes same-directory `.tmp` rewrite artifacts that an interrupted
#   sdist rewrite may leave behind, so no temporary build file survives in the
#   working tree. Idempotent: absent entries are skipped. Time complexity O(n)
#   over `dist` entry count.
# @return {int} 0 on success; 1 when a removal fails.
# @satisfies DES-061, REQ-148
remove_generated_temp_files() {
    local artifact

    if [ ! -d "${DIST_DIR}" ]; then
        return 0
    fi
    for artifact in "${DIST_DIR}"/*.tmp; do
        rm -f -- "${artifact}" || return 1
    done
    return 0
}

# @brief Remove bytecode caches created under the source tree.
# @details Deletes every `__pycache__` directory under `src` that interpreter
#   startup or the packaging toolchain may create, so no generated bytecode
#   survives in the working tree. Idempotent. Time complexity O(n) over removed
#   directory-tree entries.
# @return {int} 0 on success; 1 when a removal fails.
# @satisfies DES-061, REQ-148
remove_pycache_trees() {
    local cache_dir
    local cache_dirs

    if [ ! -d "src" ]; then
        return 0
    fi
    cache_dirs=$(find src -type d -name __pycache__ -print) || return 1
    if [ -n "${cache_dirs}" ]; then
        while IFS= read -r cache_dir; do
            rm -rf -- "${cache_dir}" || return 1
        done <<< "${cache_dirs}"
    fi
    return 0
}

# @brief Remove every intermediate artifact produced by the build process.
# @details Consolidates post-build repository hygiene: intermediate `build/` and
#   `src/shellscripts.egg-info/` trees, build-tool `dist/.gitignore` metadata,
#   leftover `dist` temporary rewrite files, and `src` bytecode caches. Invoked
#   after packaging and from the EXIT trap, so every termination path leaves
#   the working tree free of generated residue while validated deliverables
#   stay in `dist/`. Prints one parser-stable `clean` evidence line. Idempotent.
#   Time complexity O(n) over removed entries.
# @pre Current directory equals the repository root.
# @post No intermediate build artifact remains in the working tree.
# @return {int} 0 on success; 1 when a tracked entry or a removal blocks.
# @satisfies DES-045, DES-052, DES-061, REQ-141, REQ-148
clean_build_residue() {
    remove_intermediate_build_trees || return 1
    remove_generated_dist_metadata || return 1
    remove_generated_temp_files || return 1
    remove_pycache_trees || return 1
    printf 'clean: build src/shellscripts.egg-info dist:.gitignore dist:*.tmp src:__pycache__\n'
    return 0
}

# @brief Remove setuptools-generated metadata members from every sdist archive.
# @details Removes the `setup.cfg`, `MANIFEST.in`, and `src/shellscripts.egg-info/`
#   tree from every sdist. Setuptools writes `setup.cfg` and copies the egg-info
#   tree unconditionally, and `MANIFEST.in` is build configuration rather than
#   runtime content. The embedded Python program rewrites each sdist through a
#   same-directory temporary archive that replaces the original atomically; the
#   temporary archive is removed on failure. The gzip header modification time
#   is pinned to `SOURCE_DATE_EPOCH` and the gzip file name is left empty, so
#   the rewritten archive bytes do not depend on the wall clock. Every member
#   mtime is pinned to `SOURCE_DATE_EPOCH` because setuptools writes build-time
#   mtimes into the sdist; source PAX headers carrying the original mtime are
#   cleared so the pinned value is emitted. Member mode and ownership are
#   copied unchanged.
#   Time complexity O(n) over sdist size.
# @pre `SOURCE_DATE_EPOCH` is exported and matches `^[0-9]+$`.
# @return {int} 0 on success; 1 when a rewrite fails.
# @satisfies DES-053, REQ-146
strip_sdist_generated_members() {
    local code

    code='
"""Rewrite sdist archives without setuptools-generated metadata members."""
import glob
import gzip
import os
import sys
import tarfile

GENERATED_NAMES = ("setup.cfg", "MANIFEST.in", "src/shellscripts.egg-info")


def is_generated(name):
    """Return True when an archive member is generated metadata.

    Args:
        name: Archive member path including the sdist root directory.

    Returns:
        True when the member must be removed from the sdist.
    """
    rel = name.split("/", 1)[1] if "/" in name else ""
    return rel in GENERATED_NAMES or rel.startswith(
        GENERATED_NAMES[-1] + "/")


def rewrite(path, epoch):
    """Rewrite one sdist without generated members, atomically.

    Args:
        path: Sdist archive path replaced in place.
        epoch: Integer SOURCE_DATE_EPOCH written to the gzip header.

    Raises:
        OSError: When reading, writing, or replacing the archive fails.
    """
    temp = path + ".tmp"
    try:
        with open(temp, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               mtime=epoch) as gz:
                with tarfile.open(fileobj=gz, mode="w") as target:
                    with tarfile.open(path, "r:gz") as source:
                        for member in source.getmembers():
                            if is_generated(member.name):
                                continue
                            member.mtime = epoch
                            member.pax_headers = {}
                            payload = None
                            if member.isfile():
                                payload = source.extractfile(member)
                            target.addfile(member, payload)
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise


def main(dist_dir, epoch):
    """Rewrite every sdist archive found in one directory.

    Args:
        dist_dir: Directory containing `*.tar.gz` sdist archives.
        epoch: Integer SOURCE_DATE_EPOCH value.
    """
    pattern = os.path.join(dist_dir, "*.tar.gz")
    for path in sorted(glob.glob(pattern)):
        rewrite(path, epoch)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
'
    if ! "${PYTHON_BIN}" -c "${code}" "${DIST_DIR}" "${SOURCE_DATE_EPOCH}"; then
        log_error "Unable to strip generated metadata members from sdist archives."
        return 1
    fi
    return 0
}

# @brief Execute the selected distribution build tool.
# @details Runs the resolved build command vector from the repository root so
#   sdist and wheel packages are written into `dist/`. Prints the resolved
#   epoch together with its source token, so the archive timestamp provenance
#   is visible in the build log. The exported SOURCE_DATE_EPOCH is inherited by
#   the build process. Time complexity O(n) over project size plus toolchain
#   latency.
# @pre `BUILD_CMD` is a non-empty command vector set by `resolve_build_tool`.
# @pre `EPOCH_SOURCE` records the resolved epoch origin.
# @return {int} 0 on success; 1 when the build tool exits non-zero.
# @satisfies DES-040, REQ-134, REQ-151
build_distributions() {
    printf 'Build tool: %s\n' "${BUILD_TOOL}"
    printf 'SOURCE_DATE_EPOCH: %s (%s)\n' "${SOURCE_DATE_EPOCH}" "${EPOCH_SOURCE}"
    "${BUILD_CMD[@]}" || return 1
    return 0
}

# @brief Execute the build tool and normalize generated dist metadata.
# @details Delegates packaging to the selected build tool, then rewrites the
#   sdist without generated members, removes the build-tool `dist/.gitignore`
#   metadata so the repository root ignore rules remain authoritative for
#   non-generated files, and removes intermediate build trees. Time complexity
#   O(n) over project size plus toolchain latency.
# @return {int} 0 when the build and metadata normalization succeed; 1
#   otherwise.
# @satisfies DES-040, DES-052, DES-053, REQ-134, REQ-141
run_distribution_build() {
    build_distributions || return 1
    strip_sdist_generated_members || return 1
    remove_generated_dist_metadata || return 1
    remove_intermediate_build_trees || return 1
    return 0
}

# @brief Validate required and forbidden members of one sdist archive.
# @details Lists archive members with `tarfile`, strips the single top-level
#   directory prefix, requires `pyproject.toml` and
#   `src/shell_scripts/__init__.py`, and rejects every member under `tests/`
#   or `src/shellscripts.egg-info/` and any `setup.cfg` or `MANIFEST.in` member.
#   Time complexity O(n) over archive member count.
# @param $1 {str} Sdist archive path.
# @return {int} 0 when the member set is compliant; 1 otherwise.
# @satisfies DES-048, DES-049, REQ-146
verify_sdist_members() {
    local artifact="$1"
    local code

    code='
"""Validate required and forbidden members of one sdist archive."""
import sys
import tarfile

REQUIRED = ("pyproject.toml", "src/shell_scripts/__init__.py")
FORBIDDEN_PREFIXES = ("tests", "src/shellscripts.egg-info")
FORBIDDEN_NAMES = ("setup.cfg", "MANIFEST.in")


def is_below(name, prefix):
    """Return True when a member equals or lies below a path prefix.

    Args:
        name: Member path relative to the sdist root directory.
        prefix: Directory or file path prefix.

    Returns:
        True when name equals prefix or starts with prefix plus a slash.
    """
    return name == prefix or name.startswith(prefix + "/")


def main(path):
    """Exit with status 1 when required or forbidden members violate rules.

    Args:
        path: Sdist archive path.
    """
    with tarfile.open(path, "r:gz") as archive:
        names = [
            member.name.split("/", 1)[1]
            for member in archive.getmembers()
            if "/" in member.name
        ]
    missing = [name for name in REQUIRED if name not in names]
    rejected = [
        name
        for name in names
        if name in FORBIDDEN_NAMES
        or any(is_below(name, prefix) for prefix in FORBIDDEN_PREFIXES)
    ]
    if missing:
        print("Missing sdist members: " + ", ".join(missing),
              file=sys.stderr)
    if rejected:
        print("Forbidden sdist members: " + ", ".join(rejected),
              file=sys.stderr)
    if missing or rejected:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
'
    if ! "${PYTHON_BIN}" -c "${code}" "${artifact}"; then
        log_error "Sdist member validation failed: ${artifact}"
        return 1
    fi
    return 0
}

# @brief Validate required and forbidden members of one wheel archive.
# @details Lists archive members with `zipfile`, requires
#   `*.dist-info/licenses/LICENSE` and a `*.dist-info/entry_points.txt` that
#   declares the `shellscripts` and `s` console scripts as exact lines, and
#   rejects every member outside the `shell_scripts/` package and
#   `*.dist-info/` directories. Time complexity O(n) over archive member count.
# @param $1 {str} Wheel archive path.
# @return {int} 0 when the member set is compliant; 1 otherwise.
# @satisfies DES-050, REQ-145
verify_wheel_members() {
    local artifact="$1"
    local code

    code='
"""Validate required and forbidden members of one wheel archive."""
import sys
import zipfile

LICENSE_SUFFIX = ".dist-info/licenses/LICENSE"
ENTRY_SUFFIX = ".dist-info/entry_points.txt"
EXPECTED_SCRIPTS = (
    "shellscripts = shell_scripts.core:main",
    "s = shell_scripts.core:main",
)


def main(path):
    """Exit with status 1 when required or forbidden members violate rules.

    Args:
        path: Wheel archive path.
    """
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        entry_files = [n for n in names if n.endswith(ENTRY_SUFFIX)]
        license_files = [n for n in names if n.endswith(LICENSE_SUFFIX)]
        entry_lines = set()
        for name in entry_files:
            text = archive.read(name).decode("utf-8")
            entry_lines.update(line.strip() for line in text.splitlines())
    rejected = [
        n
        for n in names
        if not (n.startswith("shell_scripts/")
                or n.split("/", 1)[0].endswith(".dist-info"))
    ]
    missing = []
    if not license_files:
        missing.append("*.dist-info/licenses/LICENSE")
    if not entry_files:
        missing.append("*.dist-info/entry_points.txt")
    missing.extend(
        line for line in EXPECTED_SCRIPTS if line not in entry_lines)
    if missing:
        print("Missing wheel members: " + ", ".join(missing),
              file=sys.stderr)
    if rejected:
        print("Forbidden wheel members: " + ", ".join(rejected),
              file=sys.stderr)
    if missing or rejected:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
'
    if ! "${PYTHON_BIN}" -c "${code}" "${artifact}"; then
        log_error "Wheel member validation failed: ${artifact}"
        return 1
    fi
    return 0
}

# @brief Validate generated sdist and wheel deliverables.
# @details Requires at least one non-empty `.tar.gz` sdist and one non-empty
#   `.whl` wheel, verifies archive readability with the Python standard
#   library (`tarfile` listing and `zipfile` CRC test), and checks the
#   required and forbidden archive members. Time complexity O(n) over archive
#   contents.
# @return {int} 0 when every generated archive is valid; 1 otherwise.
# @satisfies DES-046, REQ-135, REQ-145, REQ-146
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
        if ! verify_sdist_members "${artifact}"; then
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
        if ! verify_wheel_members "${artifact}"; then
            return 1
        fi
    done

    printf 'Validated artifacts: %d sdist, %d wheel\n' "${#sdists[@]}" "${#wheels[@]}"
    return 0
}

# @brief Print the final deliverable summary.
# @details Iterates every file currently present in `dist/`, including
#   preserved non-generated entries, and prints its path and human-readable
#   size, followed by the final success line. Time complexity O(n) over
#   `dist/` file count.
# @return {None} Writes summary lines to stdout.
# @satisfies DES-046, DES-047, REQ-135
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

# @brief Register termination traps before the pipeline starts.
# @details EXIT runs `on_exit` on every termination path; INT and TERM are
#   converted into conventional failure statuses (130 and 143) so the EXIT
#   trap preserves the non-zero result. Time complexity O(1).
# @return {None} Installs shell trap handlers.
# @satisfies DES-045
register_traps() {
    trap on_exit EXIT
    trap 'on_signal INT 130' INT
    trap 'on_signal TERM 143' TERM
}

register_traps

begin_phase "Phase 1: Repository root, toolchain, and build timestamp"
if ! resolve_project_root; then
    fail_phase "Unable to determine project root from build script path."
fi
PROJECT_ROOT_READY=1
resolve_python_interpreter
if ! resolve_build_tool; then
    fail_phase "Toolchain validation failed."
fi
if ! resolve_source_date_epoch; then
    fail_phase "SOURCE_DATE_EPOCH could not be resolved."
fi
pass_phase

begin_phase "Phase 2: Previous build cleanup"
if ! clean_previous_builds; then
    fail_phase "Previous build cleanup refused or failed."
fi
pass_phase

begin_phase "Phase 3: Distribution build"
if ! run_distribution_build; then
    fail_phase "Distribution build failed."
fi
pass_phase

begin_phase "Phase 4: Post-build repository hygiene"
if ! clean_build_residue; then
    fail_phase "Post-build repository hygiene failed."
fi
CLEANUP_DONE=1
pass_phase

begin_phase "Phase 5: Artifact validation"
if ! verify_artifacts; then
    fail_phase "Artifact validation failed."
fi
pass_phase

begin_phase "Phase 6: Deliverable summary"
pass_phase
print_summary

exit 0
