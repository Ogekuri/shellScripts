"""
@brief Validate release build and pre-release script contracts plus ignore rules.
@details Parses `scripts/pre-release-check.sh` and `scripts/build.sh`, asserts
  repository-root resolution, delegated build invocation, pytest execution with
  `PYTHONPATH=src`, artifact validation, previous-build cleanup, post-build
  repository hygiene, epoch resolution from the tracked `.build-epoch` file,
  cleanup safety and trap registration, repository-integrity verification,
  fail-fast semantics, evidence lines, and executable permissions. Validates
  Bash syntax via `bash -n` and probes the real `.gitignore` behavior with
  `git check-ignore --no-index`.
@satisfies TST-015, TST-021, DES-021, DES-022, DES-023, DES-024, DES-025,
  DES-026, DES-027, DES-040, DES-041, DES-042, DES-043, DES-044, DES-045,
  DES-046, DES-047, DES-060, DES-061, DES-063, DES-064, DES-065, REQ-079,
  REQ-080, REQ-081, REQ-082, REQ-134, REQ-135, REQ-136, REQ-137, REQ-138,
  REQ-139, REQ-140, REQ-141, REQ-142, REQ-143, REQ-144, REQ-148, REQ-149,
  REQ-150, REQ-151, REQ-152, REQ-153
@return {None} Pytest module scope.
"""

import pathlib
import subprocess

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PRECHECK_PATH = PROJECT_ROOT / "scripts" / "pre-release-check.sh"
BUILD_PATH = PROJECT_ROOT / "scripts" / "build.sh"
EPOCH_PATH = PROJECT_ROOT / ".build-epoch"


def _read(path: pathlib.Path) -> str:
    """
    @brief Load one tracked script file as UTF-8 text.
    @details Reads the script content for token-level structural assertions.
      Time complexity O(n) over file size.
    @param path {pathlib.Path} Script path to read.
    @return {str} Full script content.
    @throws {OSError} When the script file cannot be read.
    """

    return path.read_text(encoding="utf-8")


def test_release_scripts_exist_and_are_executable():
    """
    @brief Validate release script presence and executable permissions.
    @details Asserts both mandatory scripts exist at their required paths,
      contain non-empty content, and carry the executable bit required by the
      documented invocation contract.
    @return {None} Assertions only.
    @satisfies TST-015, DES-021, DES-040, REQ-144
    """

    assert PRECHECK_PATH.is_file()
    assert BUILD_PATH.is_file()
    assert _read(PRECHECK_PATH).strip()
    assert _read(BUILD_PATH).strip()
    assert PRECHECK_PATH.stat().st_mode & 0o111
    assert BUILD_PATH.stat().st_mode & 0o111


def test_release_scripts_pass_bash_syntax_check():
    """
    @brief Validate Bash syntax of both release scripts.
    @details Executes `bash -n` against each script and passes only when the
      parser reports no syntax errors and a zero exit status.
    @return {None} Assertions only.
    @satisfies TST-015, DES-021, DES-040
    """

    for script_path in (PRECHECK_PATH, BUILD_PATH):
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_pre_release_script_resolves_root_and_delegates_build():
    """
    @brief Validate root resolution and delegated distribution build.
    @details Asserts the pre-release script resolves the Git repository root,
      changes into it, invokes `scripts/build.sh` instead of duplicating build
      tool selection, and runs pytest with the project `src` on `PYTHONPATH`.
    @return {None} Assertions only.
    @satisfies TST-015, DES-022, DES-023, DES-024, REQ-136
    """

    content = _read(PRECHECK_PATH)
    assert "rev-parse --show-toplevel" in content
    assert 'cd -- "${PROJECT_ROOT}"' in content
    assert "bash scripts/build.sh" in content
    assert "PYTHONPATH=" in content
    assert "${PWD}/src" in content
    assert "-m pytest tests/" in content
    assert ".venv/bin/python3" in content
    assert "uv build" not in content
    assert "python3 -m build" not in content


def test_build_script_selects_tool_and_validates_dist():
    """
    @brief Validate build toolchain selection and artifact validation.
    @details Asserts `scripts/build.sh` prefers `uv build`, falls back to the
      Python `build` module, validates sdist and wheel readability with the
      standard library, preserves non-generated `dist` entries, and summarizes
      deliverables in `dist/`.
    @return {None} Assertions only.
    @satisfies TST-015, DES-040, DES-041, DES-046, REQ-134, REQ-135, REQ-141
    """

    content = _read(BUILD_PATH)
    assert "uv build" in content
    assert "-m build" in content
    assert "python3" in content
    assert 'DIST_DIR="dist"' in content
    assert "tarfile" in content
    assert "zipfile" in content
    assert "git ls-files --error-unmatch" in content
    assert "Refusing to delete tracked release artifact" not in content
    assert "non-generated" in content or "preserved" in content
    assert "BUILD SUMMARY" in content


def test_build_script_cleans_every_previous_build_and_residue():
    """
    @brief Validate previous-build cleanup and post-build hygiene phases.
    @details Asserts `scripts/build.sh` consolidates the previous-build cleanup
      as its first data-mutating phase, deletes every `dist` archive pattern of
      any version without a tracked-entry filter, executes a post-build
      repository-hygiene phase removing intermediate trees, generated metadata,
      temporary rewrite files, and `src` bytecode caches, and registers that
      hygiene through the EXIT trap.
    @return {None} Assertions only.
    @satisfies TST-015, DES-041, DES-044, DES-060, DES-061, REQ-141, REQ-148
    """

    content = _read(BUILD_PATH)
    assert "clean_previous_builds" in content
    assert "clean_build_residue" in content
    assert "remove_generated_temp_files" in content
    assert "remove_pycache_trees" in content
    assert "Phase 2: Previous build cleanup" in content
    assert "Phase 4: Post-build repository hygiene" in content
    cleanup_loop = content.split("clean_previous_builds() {", 1)[1]
    cleanup_loop = cleanup_loop.split("\n}\n", 1)[0]
    assert '"${DIST_DIR}"/*.tar.gz' in cleanup_loop
    assert '"${DIST_DIR}"/*.whl' in cleanup_loop
    assert '"${DIST_DIR}"/*.zip' in cleanup_loop
    assert '"${DIST_DIR}"/*.egg' in cleanup_loop
    assert "git ls-files" not in cleanup_loop
    assert "clean_build_residue; then" in content
    assert "remove_intermediate_build_trees || return 1" in content.split(
        "clean_build_residue() {", 1)[1]


def test_build_epoch_file_is_tracked_non_negative_integer():
    """
    @brief Validate the version-controlled archive timestamp epoch file.
    @details Asserts `.build-epoch` exists at the repository root, contains
      exactly one non-negative decimal integer line, and is re-included by the
      `.gitignore` inverse rules so it stays version-controlled.
      Time complexity O(1) over file size.
    @return {None} Assertions only.
    @satisfies TST-015, DES-063, DES-064
    """

    assert EPOCH_PATH.is_file()
    epoch_text = _read(EPOCH_PATH)
    assert epoch_text.strip().isdigit(), f"non-decimal build epoch: {epoch_text!r}"
    assert epoch_text == f"{int(epoch_text)}\n"

    epoch_result = _check_ignore(".build-epoch")
    assert epoch_result.returncode == 0, epoch_result.stdout
    assert _matched_rule(epoch_result).startswith("!"), epoch_result.stdout


def test_build_script_resolves_epoch_from_tracked_file():
    """
    @brief Validate epoch resolution rules in the build pipeline.
    @details Asserts `scripts/build.sh` reads `SOURCE_DATE_EPOCH` from the
      tracked `.build-epoch` file when the variable is unset, still honors an
      explicitly supplied value, never derives the epoch from Git commit
      metadata, and prints the resolved value with its source token.
    @return {None} Assertions only.
    @satisfies TST-015, DES-063, REQ-149, REQ-150, REQ-151
    """

    content = _read(BUILD_PATH)
    assert 'EPOCH_FILE=".build-epoch"' in content
    assert 'EPOCH_SOURCE="environment"' in content
    assert 'head -n 1 -- "${EPOCH_FILE}"' in content
    assert 'log_error "Missing build epoch file: ${EPOCH_FILE}"' in content
    assert "SOURCE_DATE_EPOCH: %s (%s)" in content
    assert "git log -1 --format=%ct" not in content
    assert "format=%ct" not in content


def test_pre_release_script_enforces_fail_fast_and_evidence_lines():
    """
    @brief Validate fail-fast semantics and evidence-line format.
    @details Asserts the script prints `PASS:`, `FAIL:`, and `SKIP:` evidence
      lines, aborts with exit code `1` naming the first failed check, and exits
      `0` only through the all-checks-passed summary path.
    @return {None} Assertions only.
    @satisfies TST-015, REQ-079, REQ-080, REQ-142, REQ-143
    """

    content = _read(PRECHECK_PATH)
    assert "PASS: " in content
    assert "FAIL: " in content
    assert "SKIP: " in content
    assert "exit 1" in content
    assert "exit 0" in content
    assert "Pre-release check FAILED at check: " in content
    assert "Pre-release check PASSED" in content
    assert "Mandatory checks passed: " in content
    assert "Non-applicable checks skipped: " in content


def test_pre_release_script_cleans_and_verifies_repository_integrity():
    """
    @brief Validate cleanup traps, safety guard, and integrity verification.
    @details Asserts `cleanup_artifacts` is registered through the `EXIT` trap
      and signal traps, removes `build`, `.pytest_cache`,
      `src/shellscripts.egg-info`, `__pycache__` directories, and untracked
      `dist` archives, refuses to
      remove tracked files, and compares post-cleanup repository state with the
      pre-run baseline.
    @return {None} Assertions only.
    @satisfies TST-015, DES-026, DES-027, DES-043, DES-044, DES-045, REQ-081,
      REQ-082, REQ-137, REQ-138, REQ-139
    """

    content = _read(PRECHECK_PATH)
    assert "cleanup_artifacts" in content
    assert "trap on_exit EXIT" in content
    assert "trap 'handle_signal INT 130' INT" in content
    assert "trap 'handle_signal TERM 143' TERM" in content
    assert "MANAGED_PATHS=(build .pytest_cache src/shellscripts.egg-info)" in content
    assert "find src tests -type d -name __pycache__" in content
    assert (
        "clean: build .pytest_cache src/shellscripts.egg-info __pycache__ "
        "dist:untracked-archives"
    ) in content
    assert "git ls-files --" in content
    assert "git status --porcelain=v1 --untracked-files=no" in content
    assert "BASELINE_TRACKED" in content
    assert "BASELINE_UNTRACKED" in content
    assert "assert_safe_cleanup_targets" in content
    assert "list_untracked_dist_archives" in content
    assert "collect_tracked_nonmanaged" in content


def test_pre_release_script_records_artifact_checks():
    """
    @brief Validate mandatory artifact and test-suite checks.
    @details Asserts the pre-release pipeline validates the unit-test suite,
      verifies sdist and wheel presence and readability, and runs the cleanup
      and repository-integrity checks in the success path.
    @return {None} Assertions only.
    @satisfies TST-015, DES-025, DES-044, REQ-136, REQ-138
    """

    content = _read(PRECHECK_PATH)
    assert 'run_check "unit-tests"' in content
    assert 'run_check "build"' in content
    assert 'run_check "artifacts"' in content
    assert 'run_check "cleanup"' in content
    assert 'run_check "repository-integrity"' in content
    assert 'dist"/*.tar.gz' in content
    assert 'dist"/*.whl' in content
    assert '"scripts/pre-release-check.sh" "scripts/build.sh"' in content
    assert '".build-epoch"' in content
    assert "scripts/clean.sh" not in content


def test_pre_release_script_removes_and_verifies_preexisting_artifacts():
    """
    @brief Validate pre-build removal and verification of stale dist archives.
    @details Asserts the pre-release pipeline removes every top-level `dist`
      sdist, wheel, zip, and egg archive with the same archive set used by the
      `scripts/build.sh` bootstrap removal without a Git-tracking filter,
      verifies that no release archive remains, prints `PASS`/`FAIL` evidence
      for both steps, and executes both steps before the delegated build.
      Time complexity O(1) over parsed script content.
    @return {None} Assertions only.
    @satisfies TST-021, DES-065, REQ-152, REQ-153
    """

    content = _read(PRECHECK_PATH)
    build_content = _read(BUILD_PATH)
    archive_patterns = ("*.tar.gz", "*.whl", "*.zip", "*.egg")

    removal_body = content.split(
        "remove_preexisting_release_artifacts() {", 1
    )[1]
    removal_body = removal_body.split("\n}\n", 1)[0]
    verification_body = content.split(
        "check_preexisting_release_artifacts() {", 1
    )[1]
    verification_body = verification_body.split("\n}\n", 1)[0]
    build_cleanup_body = build_content.split("clean_previous_builds() {", 1)[1]
    build_cleanup_body = build_cleanup_body.split("\n}\n", 1)[0]

    for pattern in archive_patterns:
        assert pattern in removal_body
        assert pattern in verification_body
        assert pattern in build_cleanup_body
    assert "git ls-files" not in removal_body
    assert "rm -f --" in removal_body
    assert "Pre-existing release artifacts remain in dist/" in verification_body

    assert "Phase 5: Pre-existing release artifact removal" in content
    assert (
        'run_check "previous-release-artifacts-removal" '
        "remove_preexisting_release_artifacts"
    ) in content
    assert (
        'run_check "pre-existing-release-artifacts" '
        "check_preexisting_release_artifacts"
    ) in content
    removal_index = content.index('"previous-release-artifacts-removal"')
    verification_index = content.index(
        '"pre-existing-release-artifacts"', removal_index
    )
    build_index = content.index('run_check "build" bash scripts/build.sh')
    assert removal_index < verification_index < build_index


def _check_ignore(relative_path: str) -> subprocess.CompletedProcess:
    """
    @brief Probe the real `.gitignore` evaluation for one repository path.
    @details Runs `git check-ignore --no-index` from the repository root without
      creating the probed path. Time complexity O(1) excluding Git startup.
    @param relative_path {str} Repository-relative path to probe.
    @return {subprocess.CompletedProcess} Completed Git invocation.
    """

    return subprocess.run(
        ["git", "check-ignore", "--no-index", "-v", relative_path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def _matched_rule(result: subprocess.CompletedProcess) -> str:
    """
    @brief Extract the last matching `.gitignore` pattern from a probe result.
    @details Parses the `<file>:<line>:<pattern>\t<path>` verbose format and
      returns the pattern token so negated (`!`) and excluding rules can be
      distinguished deterministically. Time complexity O(1).
    @param result {subprocess.CompletedProcess} Completed Git invocation.
    @return {str} Matched pattern token; empty string when no rule matched.
    """

    output = result.stdout.strip()
    if not output or "\t" not in output:
        return ""
    prefix = output.split("\t", 1)[0]
    return prefix.split(":", 2)[2]


def test_gitignore_reincludes_dist_deliverables():
    """
    @brief Validate inverse `.gitignore` behavior for `dist/`.
    @details Asserts `dist/` and every `dist/` file, including generated
      distribution archives, are re-included by the `!dist/**/*` rule and no
      exclusion rule matches them, by inspecting the last matching `.gitignore`
      pattern.
    @return {None} Assertions only.
    @satisfies TST-015, DES-042, REQ-140
    """

    directory_result = _check_ignore("dist/")
    assert directory_result.returncode == 0, directory_result.stdout
    assert _matched_rule(directory_result).startswith("!"), directory_result.stdout

    sdist_result = _check_ignore("dist/shellscripts-0.26.0.tar.gz")
    assert sdist_result.returncode == 0, sdist_result.stdout
    assert _matched_rule(sdist_result).startswith("!"), sdist_result.stdout

    wheel_result = _check_ignore("dist/shellscripts-0.26.0-py3-none-any.whl")
    assert wheel_result.returncode == 0, wheel_result.stdout
    assert _matched_rule(wheel_result).startswith("!"), wheel_result.stdout

    documentation_result = _check_ignore("dist/RELEASE-NOTES.md")
    assert documentation_result.returncode == 0, documentation_result.stdout
    assert _matched_rule(documentation_result).startswith("!"), documentation_result.stdout


def test_gitignore_has_no_dist_targeting_exclusion_rules():
    """
    @brief Validate absence of dist-targeting exclusion rules in `.gitignore`.
    @details Parses every non-comment `.gitignore` rule and asserts that no
      exclusion (non-negated) rule targets a `dist` path, and that the
      `!dist/` and `!dist/**/*` re-include rules are present. Time complexity
      O(n) over rule count.
    @return {None} Assertions only.
    @satisfies TST-015, DES-042, REQ-140
    """

    gitignore_text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    rules = [
        line.strip()
        for line in gitignore_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    dist_exclusions = [
        rule
        for rule in rules
        if not rule.startswith("!") and rule.lstrip("/").startswith("dist")
    ]
    assert dist_exclusions == []
    assert "!dist/" in rules
    assert "!dist/**/*" in rules
