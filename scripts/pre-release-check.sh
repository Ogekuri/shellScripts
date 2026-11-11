#!/bin/bash
# VERSION: 0.26.0
# AUTHORS: Ogekuri
# Pre-release verification pipeline for shellScripts.

# @file scripts/pre-release-check.sh
# @brief Run every mandatory readiness check required before a release.
# @details Resolves the Git repository root from the script location, captures
#   the pre-run tracked and non-managed untracked repository state, validates
#   cleanup safety, project structure, executable bits, toolchain, Bash and
#   Python syntax, optional configured static-quality tools, the pytest suite,
#   the distribution build delegated to `scripts/build.sh`, and the generated
#   release archives. Generated artifacts are removed through an EXIT/INT/TERM
#   trap on every termination path, then the repository state is compared with
#   the pre-run baseline. The script prints phase headers plus `PASS`/`FAIL`/
#   `SKIP` evidence lines and a final summary, exits `1` on the first failed
#   mandatory check, and exits `0` only when every check passes, cleanup
#   succeeds, and no repository drift is detected.
# @satisfies DES-021, DES-022, DES-023, DES-024, DES-025, DES-026, DES-027,
#   DES-043, DES-044, DES-045, DES-047, DES-054, REQ-079, REQ-080, REQ-081, REQ-082,
#   REQ-136, REQ-137, REQ-138, REQ-139, REQ-142, REQ-143, REQ-144

set -Eeuo pipefail
shopt -s nullglob

MANAGED_PATHS=(build .pytest_cache src/shellscripts.egg-info)
PYTHON_BIN=""
PROJECT_ROOT=""
FAILED_CHECK=""
SUMMARY_PRINTED=0
CLEANUP_ALLOWED=0
CLEANUP_DONE=0
CLEANUP_FAILED=0
CHECKS_PASSED=0
CHECKS_SKIPPED=0
BASELINE_TRACKED=""
BASELINE_UNTRACKED=""

# @brief Resolve the repository root and change into it.
# @details Derives the script directory from `BASH_SOURCE[0]`, resolves the
#   parent project directory, asks Git for the canonical working-tree root,
#   and changes the current directory to that root so the pipeline works from
#   any invocation directory and with paths containing spaces. Time
#   complexity O(1) excluding Git startup latency.
# @return {int} 0 on success; 1 when the Git root cannot be resolved.
# @satisfies DES-022, REQ-136
resolve_project_root() {
    local script_path
    local base_dir

    script_path=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P) || return 1
    base_dir=$(CDPATH= cd -- "${script_path}/.." 2>/dev/null && pwd -P) || return 1
    PROJECT_ROOT=$(git -C "${base_dir}" rev-parse --show-toplevel 2>/dev/null) || return 1
    if [ -z "${PROJECT_ROOT}" ]; then
        return 1
    fi
    cd -- "${PROJECT_ROOT}"
}

# @brief Print one labeled phase header.
# @details Centralizes the phase-header format so pipeline logs are
#   parser-stable and every mandatory phase is clearly delimited. Time
#   complexity O(1).
# @param $1 Phase title text.
# @return {None} Writes one stdout line.
# @satisfies DES-047, REQ-142
log_phase() {
    printf '\n==> %s\n' "$1"
}

# @brief Print one diagnostic error line to stderr.
# @details Keeps every failure message on the error stream with a fixed
#   `ERROR: ` prefix so callers and CI logs can classify failures. Time
#   complexity O(1).
# @param $1 Diagnostic text.
# @return {None} Writes one stderr line.
# @satisfies DES-047, REQ-142
log_error() {
    printf 'ERROR: %s\n' "$1" >&2
}

# @brief Execute one mandatory check and record PASS/FAIL evidence.
# @details Prints a `==> Running check` header, executes the provided command
#   vector, prints `PASS: <name>` and increments the passed-check counter on
#   success, or prints `FAIL: <name>` and records the failed check name.
#   Time complexity O(1) plus executed command latency.
# @param $1 Check name used in evidence and summary lines.
# @param $2... Command vector executed for this check.
# @return Propagates the executed command exit status.
# @satisfies REQ-079, REQ-080, REQ-142
run_check() {
    local check_name="$1"
    shift
    printf '==> Running check: %s\n' "${check_name}"
    if "$@"; then
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        printf 'PASS: %s\n' "${check_name}"
        return 0
    fi
    FAILED_CHECK="${check_name}"
    printf 'FAIL: %s\n' "${check_name}"
    return 1
}

# @brief Record one non-applicable check as skipped.
# @details Prints a `SKIP: <name> (<reason>)` evidence line and increments the
#   skipped-check counter without counting the check as passed. Time
#   complexity O(1).
# @param $1 Check name.
# @param $2 Non-applicability reason.
# @return {None} Writes one stdout line.
# @satisfies DES-047, REQ-142, REQ-143
skip_check() {
    local check_name="$1"
    local reason="$2"
    CHECKS_SKIPPED=$((CHECKS_SKIPPED + 1))
    printf '==> Running check: %s\n' "${check_name}"
    printf 'SKIP: %s (%s)\n' "${check_name}" "${reason}"
}

# @brief Abort the pipeline after the first failed check.
# @details Runs generated-artifact cleanup when preflight allowed it and it
#   has not run yet, preserving the original failed result even when cleanup
#   also fails, then prints one parser-stable failure summary line naming the
#   failed check and terminates with exit code 1. Time complexity O(n) over
#   removed artifact entries.
# @return Does not return; exits the process with status 1.
# @satisfies DES-045, REQ-079, REQ-137, REQ-142
fail_fast() {
    if [ "${CLEANUP_ALLOWED}" -eq 1 ] && [ "${CLEANUP_DONE}" -eq 0 ]; then
        CLEANUP_DONE=1
        if ! cleanup_artifacts; then
            CLEANUP_FAILED=1
            log_error "Generated-artifact cleanup failed."
        fi
    fi
    SUMMARY_PRINTED=1
    printf 'Pre-release check FAILED at check: %s\n' "${FAILED_CHECK}"
    exit 1
}

# @brief Collect untracked files outside the managed artifact paths.
# @details Lists Git-visible untracked files and filters out the managed
#   build/test/release paths plus `__pycache__` trees so preexisting generated
#   output cannot be mistaken for repository drift. Time complexity O(n) over
#   untracked file count.
# @return {str} Newline-separated filtered path list.
# @satisfies DES-044, REQ-138
collect_untracked_nonmanaged() {
    git ls-files --others --exclude-standard | awk '
        /^(dist|build|\.pytest_cache|src\/shellscripts\.egg-info)\// { next }
        /(^|\/)__pycache__\// { next }
        { print }
    '
}

# @brief Capture the pre-run tracked and non-managed untracked state.
# @details Stores the tracked modification status plus the filtered untracked
#   file list in global baseline variables used by the final integrity check.
#   Time complexity O(n) over repository entry count.
# @return {int} 0 on success; non-zero when Git queries fail.
# @satisfies DES-044, REQ-138
capture_baseline() {
    BASELINE_TRACKED=$(git status --porcelain=v1 --untracked-files=no) || return 1
    BASELINE_UNTRACKED=$(collect_untracked_nonmanaged) || return 1
    return 0
}

# @brief Verify that destructive cleanup cannot remove user or tracked data.
# @details Fails when any tracked file lives under a managed artifact path or
#   inside a `__pycache__` tree, and fails when `dist` contains an untracked
#   entry that is not a generated distribution archive. Tracked `dist` entries
#   are preserved and never block cleanup. Runs before any write or delete
#   operation so unsafe repositories are reported instead of modified. Time
#   complexity O(n) over managed path entries.
# @return {int} 0 when cleanup is safe; 1 otherwise.
# @satisfies DES-043, REQ-139
assert_safe_cleanup_targets() {
    local tracked
    local entry

    tracked=$(git ls-files -- "${MANAGED_PATHS[@]}" ':(glob)**/__pycache__/**') || return 1
    if [ -n "${tracked}" ]; then
        log_error "Tracked files exist under generated-artifact paths:"
        printf '%s\n' "${tracked}" >&2
        return 1
    fi

    if [ -d "dist" ]; then
        for entry in dist/* dist/.[!.]* dist/..?*; do
            if [ ! -e "${entry}" ] && [ ! -L "${entry}" ]; then
                continue
            fi
            if [ -n "$(git ls-files -- "${entry}")" ]; then
                continue
            fi
            case "${entry}" in
                dist/.gitignore)
                    ;;
                dist/*.tar.gz|dist/*.whl|dist/*.zip|dist/*.egg)
                    ;;
                *)
                    log_error "dist contains an untracked non-generated entry: ${entry}"
                    return 1
                    ;;
            esac
        done
    elif [ -e "dist" ]; then
        log_error "dist exists but is not a directory."
        return 1
    fi
    return 0
}

# @brief List untracked generated release archives in `dist`.
# @details Enumerates top-level `dist` sdist, wheel, zip, and egg archives and
#   prints every path that Git does not track, so tracked release deliverables
#   are never selected for removal. Time complexity O(n) over `dist` entry
#   count.
# @return {str} Newline-separated untracked archive paths; empty when none.
# @satisfies DES-026, DES-054, REQ-081, REQ-082
list_untracked_dist_archives() {
    local entry

    if [ ! -d "dist" ]; then
        return 0
    fi
    for entry in dist/*.tar.gz dist/*.whl dist/*.zip dist/*.egg; do
        if [ -z "$(git ls-files -- "${entry}")" ]; then
            printf '%s\n' "${entry}"
        fi
    done
    return 0
}

# @brief Run the preflight safety validation and capture the baseline.
# @details Executes the cleanup-safety guard, records the pre-run repository
#   state, and only then enables generated-artifact cleanup for later
#   termination paths. Time complexity O(n) over repository entry count.
# @return {int} 0 when the pipeline may mutate generated paths; 1 otherwise.
# @satisfies DES-043, DES-044, REQ-138, REQ-139
preflight() {
    assert_safe_cleanup_targets || return 1
    capture_baseline || return 1
    CLEANUP_ALLOWED=1
    return 0
}

# @brief Validate the presence of mandatory project files.
# @details Checks the packaging manifest, Python package entrypoints, test
#   directory, release scripts, launcher script, and release workflow. Time
#   complexity O(n) over required path count.
# @return {int} 0 when every required path exists; 1 otherwise.
# @satisfies REQ-136
check_project_structure() {
    local required_path
    local -a required_paths=(
        "pyproject.toml"
        "src/shell_scripts/__init__.py"
        "src/shell_scripts/core.py"
        "scripts/build.sh"
        "scripts/pre-release-check.sh"
        "scripts/s.sh"
        "tests"
        ".github/workflows/release-pypi.yml"
    )

    for required_path in "${required_paths[@]}"; do
        if [ ! -e "${required_path}" ]; then
            log_error "Missing mandatory project path: ${required_path}"
            return 1
        fi
    done
    return 0
}

# @brief Validate that repository release scripts are executable.
# @details Verifies the executable bit on `scripts/pre-release-check.sh` and
#   `scripts/build.sh` so the documented invocation contract works. Time
#   complexity O(1).
# @return {int} 0 when both scripts are executable; 1 otherwise.
# @satisfies REQ-144
check_script_permissions() {
    local script
    local -a scripts=("scripts/pre-release-check.sh" "scripts/build.sh")

    for script in "${scripts[@]}"; do
        if [ ! -x "${script}" ]; then
            log_error "Script is not executable: ${script}"
            return 1
        fi
    done
    return 0
}

# @brief Resolve the Python interpreter used by the pipeline.
# @details Prefers `.venv/bin/python3` when executable and falls back to
#   `python3`, matching the repository test convention. Time complexity O(1).
# @return {None} Updates the global PYTHON_BIN value.
# @satisfies DES-023, REQ-136
resolve_python_interpreter() {
    if [ -x ".venv/bin/python3" ]; then
        PYTHON_BIN=".venv/bin/python3"
    else
        PYTHON_BIN="python3"
    fi
}

# @brief Validate the Python runtime, pytest, and one build tool.
# @details Requires Python 3.11 or newer and an importable pytest module, then
#   requires either an executable `uv` or an importable `build` module so the
#   delegated build cannot fail on a missing toolchain. Time complexity O(1)
#   excluding interpreter startup.
# @return {int} 0 when the toolchain is complete; 1 otherwise.
# @satisfies REQ-136
check_toolchain() {
    if ! "${PYTHON_BIN}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
        log_error "Python 3.11 or newer is required (resolved interpreter: ${PYTHON_BIN})."
        return 1
    fi
    if ! "${PYTHON_BIN}" -c 'import pytest' >/dev/null 2>&1; then
        log_error "pytest is not importable with ${PYTHON_BIN}."
        return 1
    fi
    if command -v uv >/dev/null 2>&1; then
        printf 'Build tool: uv\n'
        return 0
    fi
    if "${PYTHON_BIN}" -c 'import build' >/dev/null 2>&1; then
        printf 'Build tool: %s -m build\n' "${PYTHON_BIN}"
        return 0
    fi
    log_error "No supported build tool found; install uv or the Python build module."
    return 1
}

# @brief Validate Bash syntax of every repository shell script.
# @details Runs `bash -n` against each `scripts/*.sh` file without executing
#   it. Time complexity O(n) over script size.
# @return {int} 0 when every script parses; 1 otherwise.
# @satisfies REQ-136
check_bash_syntax() {
    local script
    for script in scripts/*.sh; do
        if ! bash -n "${script}"; then
            log_error "Bash syntax error: ${script}"
            return 1
        fi
    done
    return 0
}

# @brief Compile every Python source and test module.
# @details Runs `compileall` in quiet mode over `src` and `tests` to detect
#   syntax errors before the test suite executes. Generated bytecode is
#   removed by the cleanup phase. Time complexity O(n) over module size.
# @return {int} 0 when compilation succeeds; 1 otherwise.
# @satisfies REQ-136
check_python_syntax() {
    "${PYTHON_BIN}" -m compileall -q src tests
}

# @brief Run the formatter in check mode when the project configures one.
# @details Uses Ruff when `[tool.ruff]` is declared, Black when `[tool.black]`
#   is declared, and reports the check as skipped when no formatter is
#   configured. Sources are never modified. Time complexity O(n) over file
#   count.
# @return {int} 0 when the check passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_formatter() {
    if grep -Fq "[tool.ruff]" pyproject.toml; then
        run_check "format-check" "${PYTHON_BIN}" -m ruff format --check src tests
        return
    fi
    if grep -Fq "[tool.black]" pyproject.toml; then
        run_check "format-check" "${PYTHON_BIN}" -m black --check src tests
        return
    fi
    skip_check "format-check" "no formatter configuration in pyproject.toml"
}

# @brief Run the linter when the project configures one.
# @details Uses Ruff when `[tool.ruff]` is declared, Flake8 when
#   `[tool.flake8]` is declared, and reports the check as skipped otherwise.
#   Time complexity O(n) over file count.
# @return {int} 0 when the check passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_linter() {
    if grep -Fq "[tool.ruff]" pyproject.toml; then
        run_check "lint" "${PYTHON_BIN}" -m ruff check src tests
        return
    fi
    if grep -Fq "[tool.flake8]" pyproject.toml; then
        run_check "lint" "${PYTHON_BIN}" -m flake8 src tests
        return
    fi
    skip_check "lint" "no linter configuration in pyproject.toml"
}

# @brief Run the type checker when the project configures one.
# @details Uses mypy when `[tool.mypy]` is declared, Pyright when
#   `[tool.pyright]` is declared, and reports the check as skipped otherwise.
#   Time complexity O(n) over module size.
# @return {int} 0 when the check passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_type_checker() {
    if grep -Fq "[tool.mypy]" pyproject.toml; then
        run_check "type-check" "${PYTHON_BIN}" -m mypy src
        return
    fi
    if grep -Fq "[tool.pyright]" pyproject.toml; then
        run_check "type-check" pyright
        return
    fi
    skip_check "type-check" "no type-checker configuration in pyproject.toml"
}

# @brief Run dependency security checks when the project configures them.
# @details Uses Bandit when `[tool.bandit]` is declared, pip-audit when
#   `[tool.pip-audit]` is declared, and reports the check as skipped
#   otherwise. Time complexity O(n) over dependency count.
# @return {int} 0 when the check passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_security() {
    if grep -Fq "[tool.bandit]" pyproject.toml; then
        run_check "security" "${PYTHON_BIN}" -m bandit -q -r src
        return
    fi
    if grep -Fq "[tool.pip-audit]" pyproject.toml; then
        run_check "security" "${PYTHON_BIN}" -m pip_audit
        return
    fi
    skip_check "security" "no security-check configuration in pyproject.toml"
}

# @brief Run integration tests when that suite exists.
# @details Executes `tests/integration` through pytest when the directory
#   exists and reports the check as skipped otherwise. Time complexity O(n)
#   over test suite size.
# @return {int} 0 when the suite passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_integration_tests() {
    if [ -d "tests/integration" ]; then
        run_check "integration-tests" env PYTHONPATH="${PWD}/src" "${PYTHON_BIN}" -m pytest tests/integration
        return
    fi
    skip_check "integration-tests" "no tests/integration suite present"
}

# @brief Run end-to-end tests when that suite exists.
# @details Executes `tests/e2e` through pytest when the directory exists and
#   reports the check as skipped otherwise. Time complexity O(n) over test
#   suite size.
# @return {int} 0 when the suite passes or is not applicable; 1 otherwise.
# @satisfies REQ-143
check_e2e_tests() {
    if [ -d "tests/e2e" ]; then
        run_check "e2e-tests" env PYTHONPATH="${PWD}/src" "${PYTHON_BIN}" -m pytest tests/e2e
        return
    fi
    skip_check "e2e-tests" "no tests/e2e suite present"
}

# @brief Validate generated sdist and wheel release artifacts.
# @details Requires at least one non-empty sdist and one non-empty wheel in
#   `dist`, then verifies archive readability with the Python standard library
#   (`tarfile` listing and `zipfile` CRC test) independently from the build
#   script. Time complexity O(n) over archive contents.
# @return {int} 0 when the release artifacts are valid; 1 otherwise.
# @satisfies DES-025, REQ-136
check_artifacts() {
    local -a sdists=("dist"/*.tar.gz)
    local -a wheels=("dist"/*.whl)
    local artifact

    if [ "${#sdists[@]}" -eq 0 ]; then
        log_error "Missing sdist artifact (.tar.gz) in dist/."
        return 1
    fi
    if [ "${#wheels[@]}" -eq 0 ]; then
        log_error "Missing wheel artifact (.whl) in dist/."
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

    printf 'Validated release artifacts: %d sdist, %d wheel\n' "${#sdists[@]}" "${#wheels[@]}"
    return 0
}

# @brief Remove every filesystem artifact generated by the pipeline.
# @details Refuses to delete any tracked entry under the managed artifact paths,
#   then removes the `build`, `.pytest_cache`, and `src/shellscripts.egg-info`
#   paths, every untracked generated `dist` archive, and every `__pycache__`
#   directory under `src` and `tests`, and prints one parser-stable `clean`
#   evidence line. Tracked `dist` deliverables are preserved. Time complexity
#   O(n) over removed artifact-tree entries.
# @return {int} 0 when cleanup succeeds; 1 when a tracked entry blocks removal
#   or a filesystem deletion fails.
# @satisfies DES-026, DES-027, DES-054, REQ-081, REQ-082, REQ-137
cleanup_artifacts() {
    local tracked
    local path
    local pycache_dirs
    local archives

    printf '==> Cleaning generated artifacts\n'
    tracked=$(git ls-files -- "${MANAGED_PATHS[@]}" ':(glob)**/__pycache__/**') || return 1
    if [ -n "${tracked}" ]; then
        log_error "Refusing cleanup; tracked files exist under generated-artifact paths:"
        printf '%s\n' "${tracked}" >&2
        return 1
    fi

    for path in "${MANAGED_PATHS[@]}"; do
        if [ -e "${path}" ] || [ -L "${path}" ]; then
            rm -rf -- "${path}" || return 1
        fi
    done

    archives=$(list_untracked_dist_archives) || return 1
    while IFS= read -r path; do
        if [ -n "${path}" ]; then
            rm -f -- "${path}" || return 1
        fi
    done <<< "${archives}"

    pycache_dirs=$(find src tests -type d -name __pycache__ -print) || return 1
    if [ -n "${pycache_dirs}" ]; then
        while IFS= read -r path; do
            rm -rf -- "${path}" || return 1
        done <<< "${pycache_dirs}"
    fi

    printf 'clean: build .pytest_cache src/shellscripts.egg-info __pycache__ dist:untracked-archives\n'
    return 0
}

# @brief Verify repository integrity against the pre-run snapshot.
# @details Compares tracked modifications and non-managed untracked files with
#   the baseline captured before any write, and explicitly asserts that every
#   managed artifact path and every `__pycache__` directory has been removed,
#   including Git-ignored build output, and that no untracked generated `dist`
#   archive remains. Time complexity O(n) over repository
#   entry count.
# @return {int} 0 when the repository matches the safe baseline; 1 otherwise.
# @satisfies DES-044, REQ-081, REQ-082, REQ-138
check_repository_integrity() {
    local tracked_now
    local untracked_now
    local archives_now
    local path
    local pycache_dir

    tracked_now=$(git status --porcelain=v1 --untracked-files=no) || return 1
    untracked_now=$(collect_untracked_nonmanaged) || return 1

    if [ "${tracked_now}" != "${BASELINE_TRACKED}" ]; then
        log_error "Tracked-file state changed during pre-release checks."
        printf 'Baseline tracked state:\n%s\nCurrent tracked state:\n%s\n' \
            "${BASELINE_TRACKED}" "${tracked_now}" >&2
        return 1
    fi
    if [ "${untracked_now}" != "${BASELINE_UNTRACKED}" ]; then
        log_error "Untracked non-managed file state changed during pre-release checks."
        printf 'Baseline untracked state:\n%s\nCurrent untracked state:\n%s\n' \
            "${BASELINE_UNTRACKED}" "${untracked_now}" >&2
        return 1
    fi

    for path in "${MANAGED_PATHS[@]}"; do
        if [ -e "${path}" ] || [ -L "${path}" ]; then
            log_error "Generated artifact remains after cleanup: ${path}"
            return 1
        fi
    done

    archives_now=$(list_untracked_dist_archives) || return 1
    if [ -n "${archives_now}" ]; then
        log_error "Untracked generated dist archive remains after cleanup:"
        printf '%s\n' "${archives_now}" >&2
        return 1
    fi

    pycache_dir=$(find src tests -type d -name __pycache__ -print -quit) || return 1
    if [ -n "${pycache_dir}" ]; then
        log_error "Generated __pycache__ remains after cleanup: ${pycache_dir}"
        return 1
    fi
    return 0
}

# @brief Handle EXIT so cleanup never masks the original result.
# @details Runs generated-artifact cleanup when the preflight allowed it,
#   forces failure when cleanup fails after all checks passed, preserves any
#   preexisting non-zero exit status, and prints the failure summary when the
#   pipeline did not already print it. Time complexity O(n) over removed
#   artifact-tree entries.
# @return Does not return; exits with the resolved process status.
# @satisfies DES-045, REQ-137, REQ-142
on_exit() {
    local exit_code=$?
    trap - EXIT INT TERM

    if [ "${CLEANUP_ALLOWED}" -eq 1 ] && [ "${CLEANUP_DONE}" -eq 0 ]; then
        CLEANUP_DONE=1
        if ! cleanup_artifacts; then
            CLEANUP_FAILED=1
            log_error "Generated-artifact cleanup failed."
        fi
    fi

    if [ "${exit_code}" -eq 0 ] && [ "${CLEANUP_FAILED}" -ne 0 ]; then
        exit_code=1
    fi
    if [ "${exit_code}" -ne 0 ] && [ "${SUMMARY_PRINTED}" -eq 0 ]; then
        SUMMARY_PRINTED=1
        printf 'Pre-release check FAILED at check: %s\n' "${FAILED_CHECK:-unexpected-termination}"
    fi
    exit "${exit_code}"
}

# @brief Convert signal termination into a cleanup-eligible exit status.
# @details Stores a signal-specific failure marker and exits with the
#   conventional status so the EXIT trap performs artifact cleanup while the
#   failure result is preserved. Time complexity O(1).
# @param $1 Signal name token.
# @param $2 Conventional exit status.
# @return Does not return; exits the process.
# @satisfies DES-045, REQ-137
handle_signal() {
    FAILED_CHECK="signal-$1"
    exit "$2"
}

trap on_exit EXIT
trap 'handle_signal INT 130' INT
trap 'handle_signal TERM 143' TERM

log_phase "Phase 1: Repository preflight"
if ! resolve_project_root; then
    log_error "Unable to determine project root from pre-release script path."
    exit 1
fi
run_check "preflight" preflight || fail_fast
run_check "project-structure" check_project_structure || fail_fast
run_check "script-permissions" check_script_permissions || fail_fast

log_phase "Phase 2: Toolchain and syntax validation"
resolve_python_interpreter
run_check "toolchain" check_toolchain || fail_fast
run_check "bash-syntax" check_bash_syntax || fail_fast
run_check "python-syntax" check_python_syntax || fail_fast

log_phase "Phase 3: Static quality checks"
check_formatter || fail_fast
check_linter || fail_fast
check_type_checker || fail_fast
check_security || fail_fast

log_phase "Phase 4: Test suite execution"
run_check "unit-tests" env PYTHONPATH="${PWD}/src" "${PYTHON_BIN}" -m pytest tests/ || fail_fast
check_integration_tests || fail_fast
check_e2e_tests || fail_fast

log_phase "Phase 5: Distribution build and artifact validation"
run_check "build" bash scripts/build.sh || fail_fast
run_check "artifacts" check_artifacts || fail_fast

log_phase "Phase 6: Cleanup and repository integrity"
if ! run_check "cleanup" cleanup_artifacts; then
    CLEANUP_DONE=1
    CLEANUP_FAILED=1
    fail_fast
fi
CLEANUP_DONE=1
run_check "repository-integrity" check_repository_integrity || fail_fast

log_phase "Phase 7: Final summary"
printf 'Pre-release check PASSED: all mandatory checks succeeded.\n'
printf 'Mandatory checks passed: %d\n' "${CHECKS_PASSED}"
printf 'Non-applicable checks skipped: %d\n' "${CHECKS_SKIPPED}"
exit 0
