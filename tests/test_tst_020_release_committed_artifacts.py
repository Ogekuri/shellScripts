"""
@brief Validate release publication from tag-committed distributions.
@details Parses `.github/workflows/release-pypi.yml` as read-only text and
  checks tag-only release execution, exact `github.sha` checkout, the tracked
  sdist/wheel preflight, absence of distribution builds in every workflow job,
  and `dist/` inputs to attestation, GitHub Releases, and PyPI.
  Unit-under-test set: release job configuration and committed-artifact
  validation step. Call graph: each test -> `_read_workflow_text` -> workflow
  file; workflow block tests additionally call `_extract_job_block` and
  `_extract_step_block`. Level 0: `_extract_job_block`, `_extract_step_block`
  (pure parsers). Level 1: `_read_workflow_text` (filesystem read). Level 2:
  test functions (static workflow assertions). External dependency: repository
  workflow file only; no network, writes, clock, randomness, or shared state.
@satisfies TST-020, DES-056, DES-057, DES-058, DES-059, DES-062
@return {None} Pytest module scope.
"""

from pathlib import Path

# @var WORKFLOW_PATH {Path} Absolute release workflow path resolved from this test module.
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-pypi.yml"
)

# @var ARTIFACT_VALIDATION_STEP {str} Workflow step name that validates tagged-commit distribution inputs.
ARTIFACT_VALIDATION_STEP = "Verify committed distribution artifacts"


def _read_workflow_text() -> str:
    """
    @brief Read the release workflow as UTF-8 text.
    @details Reads the one repository workflow file without mutating filesystem
      state. Time complexity O(n) over workflow size.
    @pre `WORKFLOW_PATH` identifies a readable workflow file.
    @return {str} Complete workflow text.
    @throws {OSError} When the workflow file is missing or unreadable.
    @satisfies TST-020
    """
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _extract_job_block(workflow_text: str, job_name: str) -> str:
    """
    @brief Extract one top-level GitHub Actions job block.
    @details Selects the exact two-space-indented job header and returns lines
      up to the next top-level job header. Time complexity O(n) over workflow
      text.
    @param workflow_text {str} Complete workflow YAML text.
    @param job_name {str} Job key to extract.
    @return {str} Job block including its header.
    @throws {AssertionError} When the requested job is absent.
    @satisfies TST-020
    """
    lines = workflow_text.splitlines()
    start_index = next(
        (index for index, line in enumerate(lines) if line == f"  {job_name}:"),
        None,
    )
    assert start_index is not None, f"missing workflow job: {job_name}"

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        if line.startswith("  ") and not line.startswith("   ") and line.endswith(":"):
            end_index = index
            break
    return "\n".join(lines[start_index:end_index])


def _extract_job_names(workflow_text: str) -> list[str]:
    """
    @brief Extract every job key declared under the `jobs` section.
    @details Slices at the top-level `jobs:` header, then selects
      two-space-indented lines ending with `:` and strips the trailing colon,
      so the returned list exposes the complete job set. Time complexity O(n)
      over workflow lines.
    @param workflow_text {str} Complete workflow YAML text.
    @return {list[str]} Ordered job key list; empty when no job is declared.
    @satisfies TST-020, DES-062
    """
    _, _, jobs_text = workflow_text.partition("\njobs:\n")
    return [
        line.strip()[:-1]
        for line in jobs_text.splitlines()
        if line.startswith("  ")
        and not line.startswith("   ")
        and line.endswith(":")
    ]


def _extract_step_block(job_block: str, step_name: str) -> str:
    """
    @brief Extract one named step block from a job.
    @details Selects the exact six-space-indented step name and collects its
      content until the next step boundary. Time complexity O(n) over job
      block text.
    @param job_block {str} YAML text for one workflow job.
    @param step_name {str} Exact step name token.
    @return {str} Step block including its name line.
    @throws {AssertionError} When the requested step is absent.
    @satisfies TST-020
    """
    lines = job_block.splitlines()
    start_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line == f"      - name: {step_name}"
        ),
        None,
    )
    assert start_index is not None, f"missing workflow step: {step_name}"

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("      - name:"):
            end_index = index
            break
    return "\n".join(lines[start_index:end_index])


def test_release_job_runs_only_for_tags_and_checks_out_exact_commit():
    """
    @brief Verify release execution is restricted to the exact tagged commit.
    @details Requires a tag-ref job condition and explicit checkout of
      `github.sha`, preventing branch dispatch or a different ref from supplying
      the assets. Expected output: the release job contains both exact tokens.
    @return {None} Assertion-only test result.
    @satisfies TST-020, DES-058
    """
    workflow_text = _read_workflow_text()
    release_job = _extract_job_block(workflow_text, "build-release")
    checkout_step = _extract_step_block(release_job, "Checkout")

    assert "if: startsWith(github.ref, 'refs/tags/')" in release_job
    assert "ref: ${{ github.sha }}" in checkout_step


def test_release_workflow_has_no_distribution_build_execution():
    """
    @brief Verify no workflow job builds distribution archives.
    @details Regression case for the no-build release contract: rejects direct
      build-script, backend, and wheel-build commands across the complete
      workflow, including indirect invocation of the build-capable pre-check.
      Expected output: every distribution-build token is absent.
    @return {None} Assertion-only test result.
    @satisfies TST-020, DES-057
    """
    workflow_text = _read_workflow_text()
    forbidden_build_tokens = (
        "scripts/build.sh",
        "scripts/pre-release-check.sh",
        "uv build",
        "python -m build",
        "-m build",
        "pip wheel",
        "Build distributions",
    )

    for token in forbidden_build_tokens:
        assert token not in workflow_text, (
            f"distribution build invocation remains in workflow: {token}"
        )


def test_release_workflow_consumes_only_prebuilt_artifacts():
    """
    @brief Verify the workflow declares only artifact-consuming jobs.
    @details Contract guard for DES-062: the job set is exactly the branch gate
      and the release job, so no dependency synchronization, unit-test gate, or
      other build-preparatory job can run. Expected output: exact job-name set
      and absence of every preparatory command token.
    @return {None} Assertion-only test result.
    @satisfies TST-020, DES-057, DES-062
    """
    workflow_text = _read_workflow_text()
    job_names = _extract_job_names(workflow_text)

    assert job_names == ["check-branch", "build-release"], (
        f"unexpected workflow job set: {job_names}"
    )
    for forbidden_token in (
        "uv sync",
        "-m pytest",
        "astral-sh/setup-uv",
        "setup-python-uv",
        "pre-release-check",
    ):
        assert forbidden_token not in workflow_text, (
            f"build-preparatory workflow token remains: {forbidden_token}"
        )
    release_job = _extract_job_block(workflow_text, "build-release")
    assert "needs: check-branch" in release_job


def test_release_job_requires_tracked_nonempty_sdist_and_wheel():
    """
    @brief Verify tagged repository archives pass a tracked-file preflight.
    @details Requires the workflow validation step to enumerate Git-index paths
      under `dist/`, distinguish `.tar.gz` and `.whl`, require regular files
      with positive sizes, and run before provenance or publication actions.
      Expected output: both artifact classes are checked before release.
    @return {None} Assertion-only test result.
    @satisfies TST-020, DES-059
    """
    workflow_text = _read_workflow_text()
    release_job = _extract_job_block(workflow_text, "build-release")
    validation_step = _extract_step_block(
        release_job,
        ARTIFACT_VALIDATION_STEP,
    )
    attestation_step = _extract_step_block(
        release_job,
        "Attest build provenance",
    )

    for required_token in (
        '"git", "ls-files", "-z", "--", "dist"',
        '".tar.gz"',
        '".whl"',
        "path.is_file()",
        "path.stat().st_size > 0",
    ):
        assert required_token in validation_step, (
            f"committed-artifact validation is missing: {required_token}"
        )
    assert release_job.index(validation_step) < release_job.index(attestation_step)


def test_attestation_and_both_publication_channels_consume_dist():
    """
    @brief Verify every release channel uses the committed dist directory.
    @details Requires provenance attestation, GitHub Release asset creation,
      and PyPI publication to consume `dist/` without transferring or building
      alternate artifacts. Expected output: all three action inputs reference
      the checked-out distribution directory.
    @return {None} Assertion-only test result.
    @satisfies TST-020, DES-056
    """
    workflow_text = _read_workflow_text()
    release_job = _extract_job_block(workflow_text, "build-release")
    attestation_step = _extract_step_block(
        release_job,
        "Attest build provenance",
    )
    github_release_step = _extract_step_block(
        release_job,
        "Create GitHub Release and upload assets",
    )
    pypi_step = _extract_step_block(
        release_job,
        "Publish to PyPI via OIDC Trusted Publishing",
    )

    assert "subject-path: dist/*" in attestation_step
    assert "files: dist/**/*" in github_release_step
    assert "fail_on_unmatched_files: true" in github_release_step
    assert "packages-dir: dist/" in pypi_step
