"""
@brief Validate the shared YOLO CLI registry, launcher argv contracts, and
  inline help documentation.
@details HDT Generator-mode suite. Static analysis artifact:
  UUTs: `shell_scripts.commands._yolo_common.YOLO_CLI_REGISTRY` (Level 0
  constant), `shell_scripts.commands._yolo_common.print_yolo_help` (Level 0:
  pure stdout rendering), `shell_scripts.commands._yolo_common.run_yolo_cli`
  (Level 1: executable resolution, subprocess boundary),
  thin delegation in
  `shell_scripts.commands.{agy,claude,codex,copilot,opencode}.run` (Level 1),
  registry/global-help exposure (Level 0 lookups).
  External dependencies isolated: `subprocess.run`,
  `require_commands`. The YOLO launchers perform no Git repository root
  validation, so no project-root boundary exists in this module.
@satisfies TST-017, REQ-085, REQ-086, REQ-092, REQ-093, DES-030, DES-031
@return {None} Pytest module scope.
"""

import types

import pytest

import shell_scripts.commands._yolo_common as yolo_common
import shell_scripts.commands.agy as agy
import shell_scripts.commands.claude as claude
import shell_scripts.commands.codex as codex
import shell_scripts.commands.copilot as copilot
import shell_scripts.commands.opencode as opencode
import shell_scripts.core as core
from shell_scripts.commands import get_command

_HELP_LISTING_HEADER = "Registered YOLO CLIs (alphabetical order):"
_YOLO_MODULES = (agy, claude, codex, copilot, opencode)


def _expected_registry_rows() -> list[str]:
    """
    @brief Build the expected alphabetical registry help rows.
    @details Mirrors the `print_yolo_help` row format
      `  <command token> <executable> <option>` for every registry record in
      registry order.
    @return {list[str]} Expected registry rows in ascending command order.
    """

    return [
        f"  {spec.command:<9} {spec.executable} {spec.option}"
        for spec in yolo_common.YOLO_CLI_REGISTRY
    ]


def test_yolo_registry_is_alphabetically_ordered_and_complete():
    """
    @brief Validate registry completeness and alphabetical command ordering.
    @details Asserts the exact registered command token set in ascending
      alphabetical order and that every record exposes a non-empty
      executable, an executed option, and a behavioral note.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-086, DES-030
    """

    commands = [spec.command for spec in yolo_common.YOLO_CLI_REGISTRY]

    assert commands == ["agy", "claude", "codex", "copilot", "opencode"]
    assert commands == sorted(commands)
    for spec in yolo_common.YOLO_CLI_REGISTRY:
        assert spec.executable
        assert spec.option.startswith("--")
        assert spec.note


def test_yolo_registry_records_define_expected_yolo_options():
    """
    @brief Validate per-CLI executed option contracts in the registry.
    @details Asserts each registered CLI maps to its verified YOLO command
      syntax and that only the Copilot record documents an accepted
      alternative option.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-014, REQ-015, REQ-017, REQ-018, REQ-085, REQ-093
    """

    expected_options = {
        "agy": "--dangerously-skip-permissions",
        "claude": "--dangerously-skip-permissions",
        "codex": "--yolo",
        "copilot": "--yolo",
        "opencode": "--auto",
    }

    for command, option in expected_options.items():
        spec = yolo_common.get_yolo_spec(command)
        assert spec.executable == command
        assert spec.option == option

    copilot_spec = yolo_common.get_yolo_spec("copilot")
    assert copilot_spec.alternative == "--allow-all"
    assert copilot_spec.alternative_note
    for spec in yolo_common.YOLO_CLI_REGISTRY:
        if spec.command != "copilot":
            assert spec.alternative == ""
            assert spec.alternative_note == ""


@pytest.mark.parametrize(
    ("module", "args", "expected_command_tail"),
    [
        (agy, ["--flag"], ["--dangerously-skip-permissions", "--flag"]),
        (claude, ["--session"], ["--dangerously-skip-permissions", "--session"]),
        (codex, ["--x"], ["--yolo", "--x"]),
        (copilot, ["--extra"], ["--yolo", "--extra"]),
        (opencode, ["--inspect"], ["--auto", "--inspect"]),
    ],
)
def test_yolo_modules_delegate_expected_yolo_argv(
    monkeypatch,
    module,
    args,
    expected_command_tail,
):
    """
    @brief Validate thin module delegation to the shared YOLO runner.
    @details Stubs the shared launcher boundaries and asserts each thin module
      produces the fixed `[resolved_executable, option] + args` vector with
      default stdio/wait kwargs and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param module {module} Thin YOLO command module under test.
    @param args {list[str]} Forwarded command arguments.
    @param expected_command_tail {list[str]} Expected fixed and forwarded tail.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-085, REQ-014, REQ-015, REQ-017, REQ-018, REQ-064
    """

    observed = {}
    resolved_exec = "/opt/tools/resolved-cli"

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=11)

    monkeypatch.setattr(yolo_common, "require_commands", lambda *_cmds: resolved_exec)
    monkeypatch.setattr(yolo_common.subprocess, "run", _fake_run)

    result = module.run(args)

    assert result == 11
    assert observed["command"] == [resolved_exec] + expected_command_tail
    assert observed["kwargs"] == {}


def test_yolo_runner_with_empty_args_executes_fixed_yolo_vector_only(
    monkeypatch,
):
    """
    @brief Validate boundary behavior with empty forwarded arguments.
    @details Asserts that the shared runner command vector contains exactly
      the resolved executable and the YOLO option when no pass-through
      arguments are supplied.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-085
    """

    observed = {}
    resolved_exec = "/opt/tools/resolved-cli"

    def _fake_run(command, **kwargs):
        observed["command"] = command
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(yolo_common, "require_commands", lambda *_cmds: resolved_exec)
    monkeypatch.setattr(yolo_common.subprocess, "run", _fake_run)

    result = yolo_common.run_yolo_cli("agy", [])

    assert result == 0
    assert observed["command"] == [
        resolved_exec,
        "--dangerously-skip-permissions",
    ]


@pytest.mark.parametrize("module", list(_YOLO_MODULES))
def test_yolo_help_lists_registry_alphabetically_with_options(capsys, module):
    """
    @brief Validate registry documentation inside each YOLO inline help.
    @details Captures `print_help` output, isolates the registry listing
      section, and asserts every registry row with its executed option appears
      exactly once in ascending alphabetical order together with every
      behavioral note and executed option.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @param module {module} Thin YOLO command module under test.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-086, REQ-092
    """

    module.print_help("0.0.0-test")

    output = capsys.readouterr().out
    assert _HELP_LISTING_HEADER in output
    listing = output.split(_HELP_LISTING_HEADER, 1)[1]
    rows = _expected_registry_rows()
    positions = [listing.index(row) for row in rows]
    assert positions == sorted(positions)
    assert len(set(positions)) == len(rows)
    for spec in yolo_common.YOLO_CLI_REGISTRY:
        assert spec.option in output
        assert spec.note in output


def test_copilot_help_documents_allow_all_alternative(capsys):
    """
    @brief Validate Copilot alternative option documentation in inline help.
    @details Asserts the `copilot` inline help documents the accepted
      `--allow-all` alternative with its behavioral note while the executed
      option remains `--yolo` and is never replaced by the alternative.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @satisfies TST-017, REQ-092, REQ-093
    """

    copilot.print_help("0.0.0-test")

    output = capsys.readouterr().out
    assert "--allow-all" in output
    copilot_spec = yolo_common.get_yolo_spec("copilot")
    assert copilot_spec.alternative_note in output
    assert copilot.SPEC.option == "--yolo"
    assert copilot.SPEC.alternative == "--allow-all"


def test_yolo_registry_and_global_help_expose_commands():
    """
    @brief Validate registry mapping and AI help section exposure for YOLO CLIs.
    @details Asserts lazy registry resolution returns each thin YOLO module
      with a non-empty description and that the global-help AI section
      contains the `agy` token.
    @return {None} Assertions only.
    @satisfies TST-017, DES-001, DES-008, DES-014, DES-031
    """

    for module in _YOLO_MODULES:
        resolved = get_command(module.SPEC.command)
        assert resolved is module
        assert module.DESCRIPTION

    ai_section = next(
        section
        for section_name, section in core.HELP_SECTION_COMMANDS
        if section_name == "AI Commands"
    )
    assert "agy" in ai_section
