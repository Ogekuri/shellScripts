"""
@brief Validate release-pypi workflow PyPI publication gating contract.
@details Parses the repository workflow artifact
  `.github/workflows/release-pypi.yml` as static text and verifies that the
  PyPI publication step is gated on `master` tag membership, authenticates via
  OIDC Trusted Publishing without embedded credential secrets, retains every
  non-build release step for tag refs (PRJ-007, DES-016, DES-017),
  and validates that every `pyproject.toml` classifier is a canonical PyPI
  trove entry so upload requests cannot be rejected with metadata 400 errors
  (PRJ-007).
  Level classification: all helpers are Level 0 (pure text parsing over
  tracked static artifacts); test functions are Level 1 consumers with no
  cross-test dependencies and no network, filesystem side effects, clock,
  or randomness exposure.
@satisfies TST-013, PRJ-007, DES-016, DES-017
@return {None} Pytest module scope.
"""

import tomllib
from pathlib import Path

# @var WORKFLOW_PATH {Path} Absolute path of the release workflow artifact under verification; resolved from this test file location to remain working-directory independent.
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-pypi.yml"
)

# @var PYPI_PUBLISH_ACTION {str} Trusted-publishing action reference required for the PyPI publication step (PRJ-007, DES-017).
PYPI_PUBLISH_ACTION = "uses: pypa/gh-action-pypi-publish@release/v1"

# @var MASTER_GATE_EXPRESSION {str} Step-level condition expression gating PyPI publication on master tag membership (DES-016).
MASTER_GATE_EXPRESSION = "if: needs.check-branch.outputs.is_master == 'true'"

# @var EMBEDDED_CREDENTIAL_TOKENS {tuple[str, ...]} Credential/token identifiers that MUST NOT appear in the workflow (DES-017).
EMBEDDED_CREDENTIAL_TOKENS = (
    "password:",
    "PYPI_API_TOKEN",
    "pypi_token",
    "TWINE_USERNAME",
    "TWINE_PASSWORD",
)

# @var PYPROJECT_PATH {Path} Absolute path of the packaging metadata artifact whose classifiers feed PyPI upload payloads (PRJ-007).
PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"

# @var CANONICAL_TROVE_CLASSIFIERS {tuple[str, ...]} Authoritative snapshot of canonical PyPI trove classifier entries referenced by this project, verified against https://pypi.org/pypi?%3Aaction=list_classifiers; upload requests are rejected with HTTP 400 when any metadata classifier is absent from the canonical list.
CANONICAL_TROVE_CLASSIFIERS = (
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development",
)

# @var INVALID_TOPIC_CLASSIFIER {str} Non-canonical classifier rejected by PyPI with HTTP 400 (`is not a valid classifier`); kept as regression-guard evidence.
INVALID_TOPIC_CLASSIFIER = "Topic :: Software Development :: Configuration Management"

# @var RETAINED_ACTION_REFS {tuple[str, ...]} Preexisting release-step action references that MUST be retained by the PyPI migration (user-requested logic preservation).
RETAINED_ACTION_REFS = (
    "uses: actions/checkout@v7",
    "uses: actions/setup-python@v7",
    "uses: actions/attest-build-provenance@v4",
    "uses: mikepenz/release-changelog-builder-action@v6",
    "uses: softprops/action-gh-release@v3",
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
    @satisfies TST-013
    """
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _extract_step_blocks(job_block: str) -> list[str]:
    """
    @brief Split one job block into step bodies by `- name:` boundaries.
    @details Treats each line beginning with six-space indentation followed by
      `- name:` as the start of a new step body and collects subsequent lines
      until the next boundary. Time complexity O(n) over job block length.
    @param job_block {str} YAML text of one job definition.
    @return {list[str]} Step body blocks in declaration order.
    @satisfies TST-013
    """
    blocks: list[str] = []
    current_lines: list[str] = []
    for line in job_block.splitlines():
        if line.startswith("      - name:"):
            if current_lines:
                blocks.append("\n".join(current_lines))
            current_lines = [line]
        elif current_lines:
            current_lines.append(line)
    if current_lines:
        blocks.append("\n".join(current_lines))
    return blocks


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
    @satisfies TST-013
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


def test_release_workflow_artifact_exists():
    """@brief Verify the release-pypi workflow artifact is present and non-empty.

    @details Boundary case: guarantees the parsed artifact exists and matches
      the trusted-publisher workflow name before gating assertions run.
    @return {None} Asserts presence and non-emptiness only.
    @satisfies TST-013, PRJ-005
    """
    workflow_text = _read_workflow_text()

    assert WORKFLOW_PATH.is_file(), f"missing workflow artifact: {WORKFLOW_PATH}"
    assert WORKFLOW_PATH.name == "release-pypi.yml"
    assert workflow_text.strip(), "workflow artifact is empty"


def test_release_workflow_publishes_only_on_master_tags():
    """@brief Verify the PyPI publish step exists and is master-gated.

    @details Happy path for DES-016: exactly one trusted-publishing step must
      exist, must carry the `master` membership gate, and no job-level gate
      may remain on `build-release` so release steps run for any tagged branch
      (including `develop`).
    @return {None} Asserts publish-step presence, gating, and absence of job-level gate.
    @satisfies TST-013, PRJ-007, DES-016
    """
    workflow_text = _read_workflow_text()
    build_release_block = _extract_job_block(workflow_text, "build-release")
    step_blocks = _extract_step_blocks(build_release_block)

    publish_blocks = [
        block for block in step_blocks if PYPI_PUBLISH_ACTION in block
    ]
    assert len(publish_blocks) == 1, (
        "expected exactly one PyPI trusted-publishing step"
    )
    assert MASTER_GATE_EXPRESSION in publish_blocks[0], (
        "PyPI publish step is not gated on master tag membership"
    )

    job_level_gate_lines = [
        line
        for line in build_release_block.splitlines()
        if line.startswith("    if: needs.check-branch.outputs.is_master")
    ]
    assert job_level_gate_lines == [], (
        "job-level master gate must not block release steps on non-master tags"
    )


def test_release_workflow_uses_oidc_trusted_publishing_without_credentials():
    """@brief Verify OIDC authentication and absence of embedded credentials.

    @details Error/regression case for DES-017: the workflow must declare
      `id-token: write` for OIDC token minting and must not contain PyPI
      credential or API-token identifiers.
    @return {None} Asserts permission declaration and credential-token absence.
    @satisfies TST-013, DES-017
    """
    workflow_text = _read_workflow_text()

    assert "id-token: write" in workflow_text, (
        "workflow must declare id-token: write for OIDC Trusted Publishing"
    )
    for credential_token in EMBEDDED_CREDENTIAL_TOKENS:
        assert credential_token not in workflow_text, (
            f"embedded credential identifier present: {credential_token}"
        )


def test_release_workflow_retains_nonbuild_release_steps():
    """@brief Verify non-build release steps remain present after migration.

    @details Regression guard: the check-branch job, tag trigger, provenance
      attestation, changelog generation, and GitHub release publication must
      remain present, while release-job distribution-build commands are absent.
    @return {None} Asserts retained non-build references and build absence.
    @satisfies TST-013, PRJ-005, PRJ-007, DES-057
    """
    workflow_text = _read_workflow_text()

    assert "v[0-9]+.[0-9]+.[0-9]+" in workflow_text, "tag trigger pattern missing"
    assert "jobs:" in workflow_text
    assert "  check-branch:" in workflow_text, "check-branch job missing"
    build_release_block = _extract_job_block(workflow_text, "build-release")
    for build_command in ("uv build", "python -m build", "-m build"):
        assert build_command not in build_release_block, (
            f"distribution build command remains in release job: {build_command}"
        )

    for action_ref in RETAINED_ACTION_REFS:
        assert action_ref in build_release_block, (
            f"preexisting release action missing: {action_ref}"
        )


def test_pyproject_classifiers_are_canonical_pypi_trove_entries():
    """@brief Verify every packaging classifier is a canonical PyPI trove entry.

    @details Boundary/regression coverage for PyPI upload metadata: each
      `classifiers` entry in `pyproject.toml` must be present in the
      canonical trove snapshot, the previously rejected non-canonical Topic
      entry must remain absent, and the canonical replacement must be used.
    @return {None} Asserts canonical-classifier membership only.
    @satisfies TST-013, PRJ-007
    """
    with open(PYPROJECT_PATH, "rb") as project_file:
        project_metadata = tomllib.load(project_file)

    declared_classifiers = project_metadata["project"]["classifiers"]
    canonical_entries = set(CANONICAL_TROVE_CLASSIFIERS)

    assert INVALID_TOPIC_CLASSIFIER not in canonical_entries, (
        "regression guard failed: rejected classifier present in canonical list"
    )
    assert INVALID_TOPIC_CLASSIFIER not in declared_classifiers, (
        f"non-canonical classifier rejected by PyPI upload: "
        f"{INVALID_TOPIC_CLASSIFIER}"
    )
    for classifier in declared_classifiers:
        assert classifier in canonical_entries, (
            f"classifier absent from canonical PyPI trove list: {classifier}"
        )
    assert "Topic :: Software Development" in declared_classifiers
