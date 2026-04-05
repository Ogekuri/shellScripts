"""
@brief Validate CLI launcher command wrappers.
@details Verifies subprocess command vectors, project-path handling, CODEX_HOME
  environment setup, and codex auth symlink guard across cli-* and editor
  commands.
@satisfies TST-005, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019,
  REQ-020, REQ-021, REQ-043, REQ-044, REQ-064
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import pytest

import shell_scripts.commands.cli_claude as cli_claude
import shell_scripts.commands.cli_codex as cli_codex
import shell_scripts.commands.cli_copilot as cli_copilot
import shell_scripts.commands.cli_gemini as cli_gemini
import shell_scripts.commands.cli_kiro as cli_kiro
import shell_scripts.commands.cli_opencode as cli_opencode
import shell_scripts.commands.vscode_cmd as vscode_cmd
import shell_scripts.commands.vsinsider_cmd as vsinsider_cmd


def _require_symlink_capability(tmp_path: Path) -> None:
    """
    @brief Skip symlink-dependent tests when runtime lacks symlink privilege.
    @details Creates and removes a temporary symlink probe to detect whether
      the current runtime account can create symbolic links.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Test is skipped when symlink creation is unavailable.
    """

    probe_dir = tmp_path / "symlink-probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    target = probe_dir / "target"
    target.touch()
    link = probe_dir / "link"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink capability unavailable: {exc}")
    link.unlink(missing_ok=True)


def test_cli_codex_creates_auth_symlink_sets_codex_home_and_executes_expected_command(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate cli-codex creation path contract.
    @details Stubs project-root resolution and subprocess boundary, then
      validates auth-symlink creation, creation-message emission, CODEX_HOME
      assignment, command vector, and return-code propagation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-043, REQ-044, REQ-064
    """

    _require_symlink_capability(tmp_path)
    project_root = tmp_path / "project-a"
    fake_home = tmp_path / "home-a"
    project_root.mkdir(parents=True)
    fake_home.mkdir(parents=True)
    observed = {}
    observed_info = []

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=7)

    def _fake_print_info(message):
        observed_info.append(message)

    monkeypatch.setattr(cli_codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(cli_codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(cli_codex, "print_info", _fake_print_info)
    monkeypatch.setattr(cli_codex, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_codex.subprocess, "run", _fake_run)

    result = cli_codex.run(["--x"])

    expected_link = project_root / ".codex" / "auth.json"
    expected_target = fake_home / ".codex" / "auth.json"
    assert result == 7
    assert expected_link.is_symlink()
    assert expected_link.resolve(strict=False) == expected_target.resolve(strict=False)
    assert observed_info == [f"Created symlink: {expected_link} -> {expected_target}"]
    assert cli_codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == ["codex", "--yolo", "--x"]
    assert observed["kwargs"] == {}


def test_cli_codex_keeps_existing_auth_symlink_without_creation_message(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate cli-codex no-op path for compliant auth symlink.
    @details Precreates compliant project auth symlink and verifies command
      does not emit creation info while preserving subprocess execution contract.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-043, REQ-044, REQ-064
    """

    _require_symlink_capability(tmp_path)
    project_root = tmp_path / "project-b"
    fake_home = tmp_path / "home-b"
    project_root.mkdir(parents=True)
    fake_home.mkdir(parents=True)
    expected_link = project_root / ".codex" / "auth.json"
    expected_target = fake_home / ".codex" / "auth.json"
    expected_link.parent.mkdir(parents=True, exist_ok=True)
    expected_link.symlink_to(expected_target)
    observed_info = []
    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=0)

    def _fake_print_info(message):
        observed_info.append(message)

    monkeypatch.setattr(cli_codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(cli_codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(cli_codex, "print_info", _fake_print_info)
    monkeypatch.setattr(cli_codex, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_codex.subprocess, "run", _fake_run)

    result = cli_codex.run(["--z"])

    assert result == 0
    assert expected_link.is_symlink()
    assert expected_link.resolve(strict=False) == expected_target.resolve(strict=False)
    assert observed_info == []
    assert cli_codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == ["codex", "--yolo", "--z"]
    assert observed["kwargs"] == {}


def test_cli_copilot_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-copilot execution contract.
    @details Stubs project-root guard and subprocess boundary to assert command
      vector and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-015, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=11)

    monkeypatch.setattr(cli_copilot, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_copilot, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_copilot.subprocess, "run", _fake_run)

    result = cli_copilot.run(["--extra"])

    assert result == 11
    assert observed["command"] == [
        "copilot",
        "--yolo",
        "--allow-all-tools",
        "--extra",
    ]
    assert observed["kwargs"] == {}


def test_cli_gemini_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-gemini execution contract.
    @details Stubs project-root guard and subprocess boundary to assert command
      vector and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-016, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=12)

    monkeypatch.setattr(cli_gemini, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_gemini, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_gemini.subprocess, "run", _fake_run)

    result = cli_gemini.run(["--flag"])

    assert result == 12
    assert observed["command"] == ["gemini", "--yolo", "--flag"]
    assert observed["kwargs"] == {}


def test_cli_claude_executes_expected_command(monkeypatch, tmp_path):
    """
    @brief Validate cli-claude execution contract.
    @details Redirects home directory to deterministic path and asserts command
      vector includes expected Claude binary and safety flag.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-017, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=13)

    monkeypatch.setattr(cli_claude, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_claude.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(cli_claude, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_claude.subprocess, "run", _fake_run)

    result = cli_claude.run(["--session"])

    expected_bin = str(tmp_path / ".claude" / "bin" / "claude")
    assert result == 13
    assert observed["command"] == [
        expected_bin,
        "--dangerously-skip-permissions",
        "--session",
    ]
    assert observed["kwargs"] == {}


def test_cli_opencode_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-opencode execution contract.
    @details Stubs project-root guard and subprocess boundary to assert command
      vector and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-018, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=14)

    monkeypatch.setattr(cli_opencode, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_opencode, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_opencode.subprocess, "run", _fake_run)

    result = cli_opencode.run(["--inspect"])

    assert result == 14
    assert observed["command"] == ["opencode", "--inspect"]
    assert observed["kwargs"] == {}


def test_cli_kiro_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-kiro execution contract.
    @details Stubs project-root guard and subprocess boundary to assert command
      vector and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-019, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=15)

    monkeypatch.setattr(cli_kiro, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_kiro, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(cli_kiro.subprocess, "run", _fake_run)

    result = cli_kiro.run(["--ai"])

    assert result == 15
    assert observed["command"] == ["kiro-cli", "--ai"]
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
