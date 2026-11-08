"""
@brief Validate pre-release check script mandatory structure and syntax.
@details Parses `scripts/pre-release-check.sh` and asserts repository-root
  resolution, pytest invocation with `PYTHONPATH=src` and `.venv` fallback,
  `dist` cleanup, `uv build`/`python3 -m build` fallback, sdist and wheel
  artifact gates, fail-fast exit semantics, and `PASS`/`FAIL` evidence-line
  format. Validates Bash syntax via `bash -n` without executing the release
  pipeline.
@satisfies TST-015, DES-021, DES-022, DES-023, DES-024, DES-025, REQ-079,
  REQ-080
@return {None} Pytest module scope.
"""

import pathlib
import subprocess

SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "pre-release-check.sh"


def _read_script() -> str:
    """
    @brief Load the pre-release check script content.
    @details Reads the script file as UTF-8 text for token-level structural
      assertions. Time complexity O(n) over script size.
    @return {str} Full script content.
    @throws {OSError} When the script file cannot be read.
    """

    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_pre_release_script_exists_and_is_non_empty():
    """
    @brief Validate pre-release script presence at the required path.
    @details Asserts the script file exists at `scripts/pre-release-check.sh`
      and contains non-empty content, proving the mandatory pipeline
      entrypoint is implemented.
    @return {None} Assertions only.
    @satisfies TST-015, DES-021
    """

    assert SCRIPT_PATH.is_file()
    assert _read_script().strip()


def test_pre_release_script_passes_bash_syntax_check():
    """
    @brief Validate Bash syntax of the pre-release script.
    @details Executes `bash -n` against the script and passes only when the
      parser reports no syntax errors and a zero exit status.
    @return {None} Assertions only.
    @satisfies TST-015, DES-021
    """

    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_pre_release_script_resolves_repository_root():
    """
    @brief Validate repository-root resolution and execution directory.
    @details Asserts the script resolves the Git repository root via
      `git rev-parse --show-toplevel` and executes all checks from that root
      via an explicit working-directory change.
    @return {None} Assertions only.
    @satisfies TST-015, DES-022
    """

    content = _read_script()
    assert "rev-parse --show-toplevel" in content
    assert 'cd -- "${PROJECT_ROOT}"' in content


def test_pre_release_script_runs_pytest_with_src_pythonpath():
    """
    @brief Validate mandatory unit-test check invocation.
    @details Asserts the script runs pytest against `tests/`, prepends the
      project `src` directory to `PYTHONPATH`, and selects the interpreter
      via the `.venv/bin/python3`-when-present fallback to `python3`.
    @return {None} Assertions only.
    @satisfies TST-015, DES-023
    """

    content = _read_script()
    assert "PYTHONPATH=" in content
    assert "${PWD}/src" in content
    assert "-m pytest tests/" in content
    assert ".venv/bin/python3" in content


def test_pre_release_script_builds_and_verifies_artifacts():
    """
    @brief Validate mandatory build and artifact verification checks.
    @details Asserts the script removes the preexisting `dist` directory,
      builds via `uv build` with `python3 -m build` fallback, and gates the
      pipeline on at least one sdist and one wheel artifact in `dist`.
    @return {None} Assertions only.
    @satisfies TST-015, DES-024, DES-025
    """

    content = _read_script()
    assert "rm -rf -- dist" in content
    assert "uv build" in content
    assert "python3 -m build" in content
    assert 'compgen -G "dist/*.tar.gz"' in content
    assert 'compgen -G "dist/*.whl"' in content


def test_pre_release_script_enforces_fail_fast_and_evidence_lines():
    """
    @brief Validate fail-fast semantics and evidence-line format.
    @details Asserts the script prints `PASS:` and `FAIL:` evidence lines,
      aborts with exit code `1` naming the first failed check, and exits `0`
      only through the all-checks-passed summary path.
    @return {None} Assertions only.
    @satisfies TST-015, REQ-079, REQ-080
    """

    content = _read_script()
    assert "PASS: " in content
    assert "FAIL: " in content
    assert "exit 1" in content
    assert "exit 0" in content
    assert "Pre-release check FAILED at check: " in content
    assert "Pre-release check PASSED" in content
