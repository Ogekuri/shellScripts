"""
@brief Validate release workflow pytest gating contract.
@details Parses the repository workflow artifact
  `.github/workflows/release-pypi.yml` as static text and verifies that a
  dedicated `pre-release-check` job installs test dependencies without
  installing the project and runs the unit suite, and `build-release` declares
  `needs` on it, so a test failure prevents
  artifact attestation, changelog, GitHub release, and PyPI publication
  (DES-028, DES-029, REQ-083).
  Level classification: all helpers are Level 0 (pure text parsing over a
  tracked static artifact); test functions are Level 1 consumers with no
  cross-test dependencies and no network, filesystem side effects, clock,
  or randomness exposure.
@satisfies TST-016, DES-028, DES-029, REQ-083
@return {None} Pytest module scope.
"""

from pathlib import Path

# @var WORKFLOW_PATH {Path} Absolute path of the release workflow artifact under verification; resolved from this test file location to remain working-directory independent.
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-pypi.yml"
)

# @var PRECHECK_JOB_HEADER {str} Exact two-space-indented job header declaring the dedicated pre-release verification job (DES-028).
PRECHECK_JOB_HEADER = "  pre-release-check:"

# @var TEST_SUITE_COMMAND {str} Runner line that executes the project pytest suite inside the dedicated verification job (DES-028).
TEST_SUITE_COMMAND = "run: .venv/bin/python -m pytest tests/"

# @var TEST_DEPENDENCY_COMMAND {str} Runner line that synchronizes dependency groups without installing the project (DES-028).
TEST_DEPENDENCY_COMMAND = "run: uv sync --frozen --no-install-project"

# @var BUILD_RELEASE_NEEDS_LINE {str} Exact `needs` declaration that gates the release build job on the pre-release verification job (DES-029, REQ-083).
BUILD_RELEASE_NEEDS_LINE = "needs: [check-branch, pre-release-check]"

# @var FORBIDDEN_PUBLISH_ACTIONS {tuple[str, ...]} Release/publication action slugs that MUST NOT appear inside the pre-release verification job.
FORBIDDEN_PUBLISH_ACTIONS = (
    "pypa/gh-action-pypi-publish",
    "softprops/action-gh-release",
    "actions/attest-build-provenance",
)


def _read_workflow_text() -> str:
    """
    @brief Read the release workflow artifact as decoded UTF-8 text.
    @details Performs a single read of the tracked workflow file referenced by
      `WORKFLOW_PATH`; no writes, network, or environment access. Time
      complexity O(n) where n is the file byte size.
    @pre Workflow artifact exists at `WORKFLOW_PATH`.
    @return {str} Full workflow file content.
    @throws {OSError} When the workflow artifact is missing or unreadable.
    @satisfies TST-016
    """
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _extract_job_block(workflow_text: str, job_name: str) -> str:
    """
    @brief Extract one job definition block from workflow text.
    @details Slices from the two-space-indented `job_name:` header until the
      next two-space-indented job header or document end. Time complexity
      O(n) over payload length.
    @param workflow_text {str} Full workflow file content.
    @param job_name {str} Job key to extract.
    @return {str} Job block text.
    @throws {AssertionError} When the job key is absent.
    @satisfies TST-016
    """
    lines = workflow_text.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line == f"  {job_name}:":
            start_index = index
            break
    assert start_index is not None, f"missing job definition: {job_name}"

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        if line.startswith("  ") and not line.startswith("   ") and line.endswith(":"):
            end_index = index
            break
    return "\n".join(lines[start_index:end_index])


def test_release_workflow_declares_pre_release_check_job():
    """
    @brief Verify the dedicated pytest job runs before artifact publication.
    @details Asserts the `pre-release-check` job is declared before the
      `build-release` job, provisions dependencies without installing or
      building the project, and executes the repository unit suite as a runner step.
    @return {None} Assertions only.
    @satisfies TST-016, DES-028
    """
    workflow_text = _read_workflow_text()

    assert PRECHECK_JOB_HEADER in workflow_text, (
        "dedicated pre-release-check job missing from release workflow"
    )
    assert workflow_text.index(PRECHECK_JOB_HEADER) < workflow_text.index(
        "  build-release:"
    ), "pre-release-check job must be declared before build-release"

    precheck_block = _extract_job_block(workflow_text, "pre-release-check")
    assert TEST_DEPENDENCY_COMMAND in precheck_block, (
        "pre-release-check job must sync dependencies without the project"
    )
    assert TEST_SUITE_COMMAND in precheck_block, (
        "pre-release-check job must execute the pytest suite"
    )

    forbidden_release_steps = (
        "scripts/pre-release-check.sh",
        "scripts/build.sh",
        "uv build",
        "python -m build",
        "actions/attest-build-provenance@",
        "mikepenz/release-changelog-builder-action@",
        "softprops/action-gh-release@",
        "pypa/gh-action-pypi-publish@",
    )
    for forbidden_step in forbidden_release_steps:
        assert forbidden_step not in precheck_block, (
            f"pre-release-check job must not execute release steps: {forbidden_step}"
        )


def test_release_workflow_build_release_needs_pre_release_check():
    """
    @brief Verify the build-release job declares needs on the pre-release job.
    @details Asserts the exact `needs` list on `build-release` contains both
      `check-branch` and `pre-release-check`, which is the GitHub Actions
      mechanism that skips every artifact-creation and publication step when
      verification fails.
    @return {None} Assertions only.
    @satisfies TST-016, DES-029, REQ-083
    """
    workflow_text = _read_workflow_text()
    build_release_block = _extract_job_block(workflow_text, "build-release")

    assert BUILD_RELEASE_NEEDS_LINE in build_release_block, (
        "build-release job must gate on [check-branch, pre-release-check]"
    )


def test_pre_release_job_does_not_publish_or_create_release_assets():
    """
    @brief Verify the pre-release job stays verification-only.
    @details Negative/regression guard: the dedicated verification job must
      not contain PyPI publication, GitHub release, or provenance attestation
      actions, keeping all release-side effects exclusively inside the gated
      `build-release` job.
    @return {None} Assertions only.
    @satisfies TST-016, REQ-083
    """
    workflow_text = _read_workflow_text()
    precheck_block = _extract_job_block(workflow_text, "pre-release-check")

    for forbidden_action in FORBIDDEN_PUBLISH_ACTIONS:
        assert forbidden_action not in precheck_block, (
            f"verification job must not perform release-side effects: "
            f"{forbidden_action}"
        )
