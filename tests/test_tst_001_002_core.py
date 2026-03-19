"""
@brief Validate core CLI dispatch and Linux management flags.
@details Verifies empty-argument help flow, unknown-command error flow,
  and Linux-only upgrade/uninstall command construction with propagated
  return codes. Tests are deterministic and isolate subprocess boundaries.
@satisfies TST-001, TST-002, REQ-001, REQ-002, REQ-004, REQ-005
@return {None} Pytest module scope.
"""

import types

import shell_scripts.core as core


def test_main_without_args_returns_zero_and_prints_help(
    monkeypatch,
    capsys,
):
    """
    @brief Validate empty CLI invocation behavior.
    @details Forces argv to contain only program name, suppresses update
      checks, and validates that global help is emitted with return code 0.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-001, REQ-001
    """

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core.sys, "argv", ["shellscripts"])

    result = core.main()
    captured = capsys.readouterr()

    assert result == 0
    assert "Usage: shellscripts" in captured.out


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
    @details Forces Linux path and intercepts subprocess invocation to assert
      exact shell command string and return code propagation semantics.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-002, REQ-004
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
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_upgrade()

    assert result == 17
    assert observed["shell"] is True
    assert (
        observed["command"] == "uv tool install shellscripts --force "
        "--from git+https://github.com/Ogekuri/shellScripts.git"
    )


def test_do_uninstall_linux_runs_expected_uv_command(monkeypatch):
    """
    @brief Validate Linux uninstall command composition.
    @details Forces Linux path and intercepts subprocess invocation to assert
      exact shell command string and return code propagation semantics.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-002, REQ-005
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
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_uninstall()

    assert result == 9
    assert observed["shell"] is True
    assert observed["command"] == "uv tool uninstall shellscripts"
