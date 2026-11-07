"""
@brief Validate release workflow Node24 runtime pinning contract.
@details Parses the repository workflow artifact
  `.github/workflows/release-pypi.yml` as static text and verifies that every
  referenced GitHub action resolves to the approved Node24-native runtime
  mapping (CTN-006, DES-015) and that no Node20 compatibility override
  environment variables are declared anywhere in the file.
  Level classification: all helpers are Level 0 (pure text parsing over a
  tracked static artifact); test functions are Level 1 consumers with no
  cross-test dependencies and no network, filesystem side effects, clock,
  or randomness exposure.
@satisfies TST-012, CTN-006, DES-015
@return {None} Pytest module scope.
"""

import re
from pathlib import Path

# @var WORKFLOW_PATH {Path} Absolute path of the release workflow artifact under verification; resolved from this test file location to remain working-directory independent.
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-pypi.yml"
)

# @var NODE24_NATIVE_ACTION_RUNTIMES {dict[str, str]} Approved mapping of allowed action slugs to their required Node24-native runtime ref (CTN-006, DES-015).
NODE24_NATIVE_ACTION_RUNTIMES = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "astral-sh/setup-uv": "v10",
    "actions/attest-build-provenance": "v4",
    "mikepenz/release-changelog-builder-action": "v6",
    "softprops/action-gh-release": "v3",
    "pypa/gh-action-pypi-publish": "release/v1",
}

# @var NODE20_COMPATIBILITY_OVERRIDE_TOKENS {tuple[str, ...]} Transitional Node20 opt-in/opt-out environment variable names that MUST NOT appear in the workflow (TST-012 regression guard).
NODE20_COMPATIBILITY_OVERRIDE_TOKENS = (
    "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24",
    "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION",
)

# @var USES_PIN_PATTERN {re.Pattern[str]} Regex extracting `(action_slug, runtime_ref)` pairs from every `uses: <owner>/<repo>@<ref>` reference; `finditer` preserves declaration order.
USES_PIN_PATTERN = re.compile(
    r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(v\d+|release/v\d+)"
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
    @satisfies TST-012
    """
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _extract_action_pins(workflow_text: str) -> list[tuple[str, str]]:
    """
    @brief Extract ordered action-runtime pin pairs from workflow text.
    @details Applies `USES_PIN_PATTERN` over the whole payload and converts
      each `uses: <owner>/<repo>@<ref>` match into an `(action_slug, ref)`
      tuple while preserving declaration order. Time complexity O(n) over
      payload length.
    @param workflow_text {str} Full workflow file content.
    @return {list[tuple[str, str]]} Ordered `(action_slug, runtime_ref)` pairs; empty when no `uses` references exist.
    @satisfies TST-012, DES-015
    """
    return [
        (match.group(1), match.group(2))
        for match in USES_PIN_PATTERN.finditer(workflow_text)
    ]


def test_release_workflow_artifact_exists():
    """@brief Verify the release workflow artifact is present and non-empty.

    @details Boundary case for the static contract: guarantees the parsed
      artifact exists before pin assertions run, failing with an explicit
      path-bearing message otherwise.
    @return {None} Asserts presence and non-emptiness only.
    @satisfies TST-012, PRJ-005
    """
    workflow_text = _read_workflow_text()

    assert WORKFLOW_PATH.is_file(), f"missing workflow artifact: {WORKFLOW_PATH}"
    assert workflow_text.strip(), "workflow artifact is empty"


def test_release_workflow_pins_only_node24_native_action_runtimes():
    """@brief Verify every action pin matches the approved Node24-native mapping.

    @details Happy path plus boundary coverage: each extracted
      `(action_slug, ref)` pair must exist in `NODE24_NATIVE_ACTION_RUNTIMES`
      with the exact expected runtime ref, unknown action slugs are rejected,
      and the mapping must be fully covered so no approved action is silently
      dropped from the workflow.
    @return {None} Asserts bidirectional mapping conformance only.
    @satisfies TST-012, CTN-006, DES-015
    """
    workflow_text = _read_workflow_text()
    observed_pins = _extract_action_pins(workflow_text)

    expected_output = sorted(NODE24_NATIVE_ACTION_RUNTIMES.items())
    observed_slugs = [slug for slug, _ref in observed_pins]

    assert observed_pins, "no action pins parsed from workflow artifact"
    for action_slug, runtime_ref in observed_pins:
        expected_ref = NODE24_NATIVE_ACTION_RUNTIMES.get(action_slug)
        assert expected_ref is not None, f"unapproved action reference: {action_slug}"
        assert runtime_ref == expected_ref, (
            f"{action_slug}: expected Node24-native runtime {expected_ref}, "
            f"found {runtime_ref}"
        )

    assert sorted(set(observed_slugs)) == [slug for slug, _ref in expected_output], (
        "approved Node24-native action set is not fully covered by workflow pins"
    )


def test_release_workflow_has_no_node20_compatibility_overrides():
    """@brief Verify no Node20 compatibility override variables are declared.

    @details Error/regression case: the transitional opt-in and opt-out
      environment variables described by the Node20 deprecation notice must
      be absent from the workflow definition because the pipeline targets
      Node24 natively.
    @return {None} Asserts token absence only.
    @satisfies TST-012, CTN-006
    """
    workflow_text = _read_workflow_text()

    for override_token in NODE20_COMPATIBILITY_OVERRIDE_TOKENS:
        assert override_token not in workflow_text, (
            f"forbidden Node20 compatibility override present: {override_token}"
        )
