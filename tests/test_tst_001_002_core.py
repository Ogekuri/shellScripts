"""
@brief Validate core CLI dispatch and Linux management flags.
@details Verifies empty-argument help flow, unknown-command error flow,
  startup OS detection, Linux-only upgrade/uninstall command resolution from
  runtime config, and management write-config behavior. Tests are deterministic
  and isolate subprocess and filesystem boundaries.
@satisfies TST-001, TST-002, TST-009, REQ-001, REQ-002, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-066
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import shell_scripts.core as core


def test_main_without_args_returns_zero_and_prints_help(
    monkeypatch,
    capsys,
):
    """
    @brief Validate empty CLI invocation behavior.
    @details Forces argv to contain only program name, suppresses update
      checks, tracks startup OS detection call, and validates global help
      emission with return code 0.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-001, REQ-001, REQ-047, REQ-066
    """

    observed = {"detected": 0}
    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(
        core,
        "detect_runtime_os",
        lambda: observed.__setitem__("detected", observed["detected"] + 1),
    )
    monkeypatch.setattr(core.sys, "argv", ["shellscripts"])

    result = core.main()
    captured = capsys.readouterr()

    assert result == 0
    assert observed["detected"] == 1
    assert "Usage: shellscripts" in captured.out
    assert "Edit/View Commands" in captured.out
    assert "PDF Commands" in captured.out
    assert "AI Commands" in captured.out
    assert "Develop Commands" in captured.out
    assert "Image Commands" in captured.out
    assert "Video Commands" in captured.out
    assert "OS Commands" in captured.out
    assert (
        "  claude           - Launch Claude CLI with skip-permissions in the project context."
        in captured.out
    )
    assert (
        "  codex            - Launch OpenAI Codex CLI in the project context."
        in captured.out
    )
    assert (
        "  copilot          - Launch GitHub Copilot CLI in the project context."
        in captured.out
    )
    assert (
        "  gemini           - Launch Google Gemini CLI in the project context."
        in captured.out
    )
    assert (
        "  kiro             - Launch Kiro CLI in the project context." in captured.out
    )
    assert (
        "  opencode         - Launch OpenCode CLI in the project context."
        in captured.out
    )
    assert captured.out.index("Edit/View Commands") < captured.out.index("PDF Commands")
    assert captured.out.index("PDF Commands") < captured.out.index("AI Commands")
    assert captured.out.index("AI Commands") < captured.out.index("Develop Commands")
    assert captured.out.index("Develop Commands") < captured.out.index("Image Commands")
    assert captured.out.index("Image Commands") < captured.out.index("Video Commands")
    assert captured.out.index("Video Commands") < captured.out.index("OS Commands")


def test_main_unknown_command_returns_one_and_prints_error_and_help(
    monkeypatch,
    capsys,
):
    """
    @brief Validate unknown command behavior.
    @details Suppresses update checks, injects an unknown command token,
      and verifies return code 1 with explicit error and global help output.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-001, REQ-002
    """

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core.sys, "argv", ["shellscripts", "unknown-cmd"])

    result = core.main()
    captured = capsys.readouterr()

    assert result == 1
    assert "Unknown command: unknown-cmd" in captured.err
    assert "Usage: shellscripts" in captured.out


def test_do_upgrade_linux_runs_expected_uv_command(monkeypatch):
    """
    @brief Validate Linux upgrade command composition.
    @details Forces Linux path, injects runtime-config command override, and
      intercepts subprocess invocation to assert resolved command string and
      return code propagation semantics.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-002, REQ-004, REQ-045
    """

    observed = {}

    def _fake_run(command, shell=False):
        """
        @brief Mock subprocess.run for upgrade path.
        @details Captures command and shell flag, returns deterministic code.
        @param command {str} Shell command string.
        @param shell {bool} Shell execution selector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["command"] = command
        observed["shell"] = shell
        return types.SimpleNamespace(returncode=17)

    monkeypatch.setattr(core, "is_linux", lambda: True)
    monkeypatch.setattr(
        core,
        "require_shell_command_executables",
        lambda command: observed.__setitem__("checked", command),
    )
    monkeypatch.setattr(
        core,
        "get_management_command",
        lambda name: "custom-upgrade" if name == "upgrade" else "unused",
    )
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_upgrade()

    assert result == 17
    assert observed["shell"] is True
    assert observed["command"] == "custom-upgrade"
    assert observed["checked"] == "custom-upgrade"


def test_do_uninstall_linux_runs_expected_uv_command(monkeypatch):
    """
    @brief Validate Linux uninstall command composition.
    @details Forces Linux path, injects runtime-config command override, and
      intercepts subprocess invocation to assert resolved command string and
      return code propagation semantics.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-002, REQ-005, REQ-045
    """

    observed = {}

    def _fake_run(command, shell=False):
        """
        @brief Mock subprocess.run for uninstall path.
        @details Captures command and shell flag, returns deterministic code.
        @param command {str} Shell command string.
        @param shell {bool} Shell execution selector.
        @return {types.SimpleNamespace} Object with returncode field.
        """

        observed["command"] = command
        observed["shell"] = shell
        return types.SimpleNamespace(returncode=9)

    monkeypatch.setattr(core, "is_linux", lambda: True)
    monkeypatch.setattr(
        core,
        "require_shell_command_executables",
        lambda command: observed.__setitem__("checked", command),
    )
    monkeypatch.setattr(
        core,
        "get_management_command",
        lambda name: "custom-uninstall" if name == "uninstall" else "unused",
    )
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_uninstall()

    assert result == 9
    assert observed["shell"] is True
    assert observed["command"] == "custom-uninstall"
    assert observed["checked"] == "custom-uninstall"


def test_main_loads_runtime_config_before_dispatch(monkeypatch):
    """
    @brief Validate startup runtime-config loading.
    @details Suppresses update checks, tracks config loader calls, and verifies
      main flow invokes loader once before handling version flag.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-009, REQ-045
    """

    observed = {"loaded": 0}
    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(
        core,
        "load_runtime_config",
        lambda: observed.__setitem__("loaded", observed["loaded"] + 1),
    )
    monkeypatch.setattr(core.sys, "argv", ["shellscripts", "--version"])

    result = core.main()

    assert result == 0
    assert observed["loaded"] == 1


def test_main_write_config_returns_zero_and_calls_writer(monkeypatch, capsys):
    """
    @brief Validate management write-config command behavior.
    @details Forces `--write-config` flow and asserts config writer invocation
      plus success return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-009, REQ-046
    """

    observed = {}

    def _fake_write_default_runtime_config():
        """
        @brief Mock default config write operation.
        @details Stores invocation and returns deterministic target path.
        @return {Path} Mock destination path.
        """

        observed["called"] = True
        return Path("/tmp/config.json")

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core, "load_runtime_config", lambda: {})
    monkeypatch.setattr(
        core, "write_default_runtime_config", _fake_write_default_runtime_config
    )
    monkeypatch.setattr(core.sys, "argv", ["shellscripts", "--write-config"])

    result = core.main()
    output = capsys.readouterr().out

    assert result == 0
    assert observed["called"] is True
    assert "/tmp/config.json" in output


def test_main_help_lists_req_command(monkeypatch, capsys):
    """
    @brief Validate global help command index includes `req`.
    @details Forces empty-args global-help path and asserts command list
      contains `req` entry.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-048
    """

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core.sys, "argv", ["shellscripts"])

    result = core.main()
    output = capsys.readouterr().out

    assert result == 0
    assert "req" in output
