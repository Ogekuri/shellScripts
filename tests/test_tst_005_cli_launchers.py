"""
@brief Validate CLI launcher command wrappers.
@details Verifies subprocess command vectors, project-path handling, absence
  of Codex auth synchronization and `CODEX_HOME` mutation in `codex`,
  `CODEX_HOME` setup for VS Code commands, and argument pass-through contracts
  across YOLO-mode launcher commands and VS Code editor commands.
@satisfies TST-005, REQ-014, REQ-015, REQ-017, REQ-018, REQ-020, REQ-021,
  REQ-064
@return {None} Pytest module scope.
"""

import os
from pathlib import Path
import types

import pytest

import shell_scripts.commands._yolo_common as yolo_common
import shell_scripts.commands.claude as claude
import shell_scripts.commands.codex as codex
import shell_scripts.commands.copilot as copilot
import shell_scripts.commands.opencode as opencode
import shell_scripts.commands.vscode_cmd as vscode_cmd
import shell_scripts.commands.vsinsider_cmd as vsinsider_cmd


def test_codex_executes_expected_command_without_auth_synchronization(
    monkeypatch,
    tmp_path,
    capsys,
):
    """
    @brief Validate codex YOLO execution contract without auth synchronization.
    @details Stubs the shared launcher boundaries, seeds a home auth file,
      snapshots the process environment, executes `codex.run`, then asserts
      the command vector, untouched home auth payload, absent project auth
      artifact, unchanged process environment, and empty output stream.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture} Stdout capture fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-064
    """

    project_root = tmp_path / "project-a"
    fake_home = tmp_path / "home-a"
    project_root.mkdir(parents=True)
    fake_home.mkdir(parents=True)
    home_auth = fake_home / ".codex" / "auth.json"
    home_auth.parent.mkdir(parents=True, exist_ok=True)
    home_auth.write_text("home-auth-payload", encoding="utf-8")
    observed = {}
    environment_before = dict(os.environ)

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=7)

    monkeypatch.setattr(yolo_common, "require_project_root", lambda: project_root)
    monkeypatch.setattr(yolo_common, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(yolo_common.subprocess, "run", _fake_run)

    result = codex.run(["--x"])

    assert result == 7
    assert observed["command"] == ["codex", "--yolo", "--x"]
    assert observed["kwargs"] == {}
    assert home_auth.read_text(encoding="utf-8") == "home-auth-payload"
    assert not (project_root / ".codex" / "auth.json").exists()
    assert dict(os.environ) == environment_before
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("module", "pass_through", "expected_tail"),
    [
        (claude, ["--session"], ["--dangerously-skip-permissions", "--session"]),
        (codex, ["--x"], ["--yolo", "--x"]),
        (copilot, ["--extra"], ["--yolo", "--extra"]),
        (opencode, ["--inspect"], ["--auto", "--inspect"]),
    ],
)
def test_yolo_launchers_use_resolved_executable_path(
    monkeypatch,
    module,
    pass_through,
    expected_tail,
):
    """
    @brief Validate YOLO launchers execute the resolved executable path.
    @details Mocks the shared launcher boundaries so `require_commands`
      returns a deterministic resolved path, then verifies each YOLO launcher
      uses that resolved token as argv[0] followed by its fixed YOLO option
      and forwarded arguments.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param module {module} Thin YOLO launcher module under test.
    @param pass_through {list[str]} Forwarded command arguments.
    @param expected_tail {list[str]} Expected fixed and forwarded argument tail.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-015, REQ-017, REQ-018,
        REQ-055, REQ-056, REQ-064
    """

    observed = {}
    resolved_exec = r"C:\Tools\resolved-tool.cmd"

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=27)

    monkeypatch.setattr(yolo_common, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(yolo_common, "require_commands", lambda *_cmds: resolved_exec)
    monkeypatch.setattr(yolo_common.subprocess, "run", _fake_run)

    result = module.run(pass_through)

    assert result == 27
    assert observed["command"] == [resolved_exec] + expected_tail
    assert observed["kwargs"] == {}


def test_vscode_appends_project_path_and_sets_codex_home(monkeypatch):
    """
    @brief Validate vscode launcher behavior.
    @details Stubs project-root resolution and subprocess boundary to assert
      CODEX_HOME assignment, final project-path argument placement, and `cwd`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-020, REQ-021, REQ-064
    """

    project_root = Path("/tmp/project-vscode")
    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=21)

    monkeypatch.setattr(vscode_cmd, "require_project_root", lambda: project_root)
    monkeypatch.setattr(vscode_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(vscode_cmd.subprocess, "run", _fake_run)

    result = vscode_cmd.run(["--reuse-window"])

    assert result == 21
    assert vscode_cmd.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == [
        "/usr/share/code/bin/code",
        "--reuse-window",
        str(project_root),
    ]
    assert observed["kwargs"] == {"cwd": project_root}


def test_vsinsider_appends_project_path_and_sets_codex_home(monkeypatch):
    """
    @brief Validate VS Code Insiders launcher behavior.
    @details Stubs project-root resolution and subprocess boundary to assert
      CODEX_HOME assignment, final project-path argument placement, and `cwd`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-020, REQ-021, REQ-064
    """

    project_root = Path("/tmp/project-vsinsider")
    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=22)

    monkeypatch.setattr(vsinsider_cmd, "require_project_root", lambda: project_root)
    monkeypatch.setattr(vsinsider_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(vsinsider_cmd.subprocess, "run", _fake_run)

    result = vsinsider_cmd.run(["--new-window"])

    assert result == 22
    assert vsinsider_cmd.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == [
        "/usr/share/code-insiders/bin/code-insiders",
        "--new-window",
        str(project_root),
    ]
    assert observed["kwargs"] == {"cwd": project_root}
