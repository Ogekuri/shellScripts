"""
@brief Validate Antigravity CLI launcher command and inline help contract.
@details HDT Generator-mode suite. Static analysis artifact:
  UUTs: `shell_scripts.commands.agy.run` (Level 1: project-root guard,
  executable resolution, subprocess boundary),
  `shell_scripts.commands.agy.print_help` (Level 0: pure stdout rendering),
  `shell_scripts.commands.agy.AI_CLI_COMMANDS` (Level 0 constant),
  registry/global-help exposure (Level 0 lookups).
  External dependencies isolated: `subprocess.run`, `require_project_root`,
  `require_commands`. The missing-executable error path terminates through the
  shared `require_commands` helper already covered by the TST-005 policy, so no
  launcher-local error case exists in this module.
@satisfies TST-017, REQ-085, REQ-086
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import shell_scripts.commands.agy as agy
import shell_scripts.core as core
from shell_scripts.commands import get_command


def test_agy_executes_expected_command(monkeypatch):
    """
    @brief Validate agy YOLO-mode execution contract with forwarded arguments.
    @details Stubs project-root guard and subprocess boundary to assert the
      fixed command vector, argument forwarding, default stdio/wait kwargs,
      and return-code propagation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-085, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=11)

    monkeypatch.setattr(agy, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(agy, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(agy.subprocess, "run", _fake_run)

    result = agy.run(["--flag"])

    assert result == 11
    assert observed["command"] == [
        "agy",
        "--dangerously-skip-permissions",
        "--flag",
    ]
    assert observed["kwargs"] == {}


def test_agy_empty_args_execute_fixed_yolo_vector_only(monkeypatch):
    """
    @brief Validate agy boundary behavior with empty forwarded arguments.
    @details Asserts that the command vector contains exactly the executable
      and the YOLO flag when no pass-through arguments are supplied.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-085
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(agy, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(agy, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(agy.subprocess, "run", _fake_run)

    result = agy.run([])

    assert result == 0
    assert observed["command"] == ["agy", "--dangerously-skip-permissions"]


def test_agy_print_help_lists_ai_cli_tokens_alphabetically(capsys):
    """
    @brief Validate alphabetical AI CLI listing inside agy inline help.
    @details Captures `print_help` output, isolates the AI CLI listing section,
      and asserts the exact expected token set rendered once each in ascending
      alphabetical order.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-086
    """

    expected_tokens = (
        "agy",
        "claude",
        "codex",
        "copilot",
        "gemini",
        "kiro",
        "opencode",
        "pi",
    )

    agy.print_help("0.0.0-test")

    output = capsys.readouterr().out
    assert "Available AI CLIs (alphabetical order):" in output
    listing = output.split("Available AI CLIs (alphabetical order):", 1)[1]
    positions = [listing.index(f"  {token}\n") for token in expected_tokens]
    assert positions == sorted(positions)
    assert len(set(positions)) == len(expected_tokens)


def test_agy_registry_and_global_help_expose_command():
    """
    @brief Validate registry mapping and AI help section exposure for agy.
    @details Asserts lazy registry resolution returns the agy module with a
      non-empty description and that the global-help AI section contains the
      agy token.
    @return {None} Assertions only.
    @satisfies TST-017, DES-001, DES-008, DES-014
    """

    resolved = get_command("agy")

    assert resolved is agy
    assert agy.DESCRIPTION == "Launch Antigravity CLI in the project context."
    ai_section = next(
        section
        for section_name, section in core.HELP_SECTION_COMMANDS
        if section_name == "AI Commands"
    )
    assert "agy" in ai_section
