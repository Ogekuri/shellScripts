"""
@brief Validate CLI launcher command wrappers.
@details Verifies subprocess command vectors, project-path handling, CODEX_HOME
  environment setup, and codex auth file synchronization across AI launcher and
  editor commands.
  commands.
@satisfies TST-005, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019,
  REQ-020, REQ-021, REQ-043, REQ-044, REQ-064, REQ-068, REQ-069
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import pytest

import shell_scripts.commands.claude as claude
import shell_scripts.commands.codex as codex
import shell_scripts.commands.copilot as copilot
import shell_scripts.commands.gemini as gemini
import shell_scripts.commands.kiro as kiro
import shell_scripts.commands.opencode as opencode
import shell_scripts.commands.pi as pi
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


def test_codex_syncs_auth_file_sets_codex_home_and_executes_expected_command(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate codex auth-file synchronization lifecycle.
    @details Stubs project-root resolution and subprocess boundary, then
      validates home-to-project auth copy before execution, project-to-home auth
      copy after execution, CODEX_HOME assignment, command vector, and
      return-code propagation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-043, REQ-044, REQ-064
    """

    project_root = tmp_path / "project-a"
    fake_home = tmp_path / "home-a"
    project_root.mkdir(parents=True)
    fake_home.mkdir(parents=True)
    home_auth = fake_home / ".codex" / "auth.json"
    home_auth.parent.mkdir(parents=True, exist_ok=True)
    home_auth.write_text("home-auth-before", encoding="utf-8")
    project_auth = project_root / ".codex" / "auth.json"
    project_auth.parent.mkdir(parents=True, exist_ok=True)
    project_auth.write_text("project-auth-stale", encoding="utf-8")
    observed = {}
    observed_info = []

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        assert project_auth.read_text(encoding="utf-8") == "home-auth-before"
        project_auth.write_text("project-auth-after", encoding="utf-8")
        return types.SimpleNamespace(returncode=7)

    def _fake_print_info(message):
        observed_info.append(message)

    monkeypatch.setattr(codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(codex, "print_info", _fake_print_info)
    monkeypatch.setattr(codex, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(codex.subprocess, "run", _fake_run)

    result = codex.run(["--x"])

    assert result == 7
    assert not project_auth.is_symlink()
    assert project_auth.read_text(encoding="utf-8") == "project-auth-after"
    assert home_auth.read_text(encoding="utf-8") == "project-auth-after"
    assert observed_info == [
        f"Copied auth.json (global config -> project config): {home_auth} -> {project_auth}",
        f"Copied auth.json (project config -> global config): {project_auth} -> {home_auth}",
    ]
    assert codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == ["codex", "--yolo", "--x"]
    assert observed["kwargs"] == {}


def test_codex_replaces_auth_symlink_paths_with_synced_files(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate codex overwrite contract for auth symlink destinations.
    @details Precreates project and home auth paths as symlinks, then verifies
      synchronization replaces both symlinks with copied file payloads while
      preserving subprocess execution contract.
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
    project_auth = project_root / ".codex" / "auth.json"
    project_auth.parent.mkdir(parents=True, exist_ok=True)
    project_auth_target = project_root / "project-auth-target.txt"
    project_auth_target.write_text("project-auth-target", encoding="utf-8")
    project_auth.symlink_to(project_auth_target)
    home_auth = fake_home / ".codex" / "auth.json"
    home_auth.parent.mkdir(parents=True, exist_ok=True)
    home_auth_target = fake_home / "home-auth-target.txt"
    home_auth_target.write_text("home-auth-before", encoding="utf-8")
    home_auth.symlink_to(home_auth_target)
    observed = {}
    observed_info = []

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        assert project_auth.read_text(encoding="utf-8") == "home-auth-before"
        project_auth.write_text("project-auth-after", encoding="utf-8")
        return types.SimpleNamespace(returncode=0)

    def _fake_print_info(message):
        observed_info.append(message)

    monkeypatch.setattr(codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(codex, "print_info", _fake_print_info)
    monkeypatch.setattr(codex, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(codex.subprocess, "run", _fake_run)

    result = codex.run(["--z"])

    assert result == 0
    assert not project_auth.is_symlink()
    assert project_auth.read_text(encoding="utf-8") == "project-auth-after"
    assert not home_auth.is_symlink()
    assert home_auth.read_text(encoding="utf-8") == "project-auth-after"
    assert observed_info == [
        f"Copied auth.json (global config -> project config): {home_auth} -> {project_auth}",
        f"Copied auth.json (project config -> global config): {project_auth} -> {home_auth}",
    ]
    assert codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["command"] == ["codex", "--yolo", "--z"]
    assert observed["kwargs"] == {}


def test_copilot_executes_expected_command(monkeypatch):
    """
    @brief Validate copilot execution contract.
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

    monkeypatch.setattr(copilot, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(copilot, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(copilot.subprocess, "run", _fake_run)

    result = copilot.run(["--extra"])

    assert result == 11
    assert observed["command"] == [
        "copilot",
        "--yolo",
        "--allow-all-tools",
        "--no-auto-update",
        "--extra",
    ]
    assert observed["kwargs"] == {}


def test_gemini_executes_expected_command(monkeypatch):
    """
    @brief Validate gemini execution contract.
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

    monkeypatch.setattr(gemini, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(gemini, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(gemini.subprocess, "run", _fake_run)

    result = gemini.run(["--flag"])

    assert result == 12
    assert observed["command"] == ["gemini", "--yolo", "--flag"]
    assert observed["kwargs"] == {}


def test_claude_executes_expected_command(monkeypatch, tmp_path):
    """
    @brief Validate claude execution contract.
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

    monkeypatch.setattr(claude, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(claude.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(claude, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(claude.subprocess, "run", _fake_run)

    result = claude.run(["--session"])

    expected_bin = str(tmp_path / ".claude" / "bin" / "claude")
    assert result == 13
    assert observed["command"] == [
        expected_bin,
        "--dangerously-skip-permissions",
        "--session",
    ]
    assert observed["kwargs"] == {}


def test_opencode_executes_expected_command(monkeypatch):
    """
    @brief Validate opencode execution contract.
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

    monkeypatch.setattr(opencode, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(opencode, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(opencode.subprocess, "run", _fake_run)

    result = opencode.run(["--inspect"])

    assert result == 14
    assert observed["command"] == ["opencode", "--inspect"]
    assert observed["kwargs"] == {}


def test_kiro_executes_expected_command(monkeypatch):
    """
    @brief Validate kiro execution contract.
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

    monkeypatch.setattr(kiro, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(kiro, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(kiro.subprocess, "run", _fake_run)

    result = kiro.run(["--ai"])

    assert result == 15
    assert observed["command"] == ["kiro-cli", "--ai"]
    assert observed["kwargs"] == {}


def test_pi_appends_default_tools_when_option_is_absent(monkeypatch):
    """
    @brief Validate pi command default tools append behavior.
    @details Stubs project-root guard and subprocess boundary to assert default
      `--tools` parameter is appended only when CLI args do not include
      `--tools` option tokens.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-068, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=16)

    monkeypatch.setattr(pi, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(pi, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(pi.subprocess, "run", _fake_run)

    result = pi.run(["--agent", "coder"])

    assert result == 16
    assert observed["command"] == [
        "pi",
        "--agent",
        "coder",
        "--tools",
        "read,bash,edit,write,grep,find,ls",
    ]
    assert observed["kwargs"] == {}


@pytest.mark.parametrize(
    "tools_args",
    [
        ["--tools", "read,bash"],
        ["--tools=read,bash"],
    ],
)
def test_pi_preserves_tools_override_without_appending_default(
    monkeypatch,
    tools_args,
):
    """
    @brief Validate pi command explicit tools override behavior.
    @details Verifies argument forwarding remains unchanged when any `--tools`
      token is present, and confirms default tools argument is not appended.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tools_args {list[str]} Explicit tools-option argument vectors.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-069, REQ-064
    """

    observed = {}

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=19)

    monkeypatch.setattr(pi, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(pi, "require_commands", lambda *cmds: cmds[0])
    monkeypatch.setattr(pi.subprocess, "run", _fake_run)

    result = pi.run(tools_args + ["--mode", "fast"])

    assert result == 19
    assert observed["command"] == ["pi"] + tools_args + ["--mode", "fast"]
    assert observed["kwargs"] == {}


@pytest.mark.parametrize(
    ("module", "args", "expected_tail"),
    [
        (
            copilot,
            ["--extra"],
            ["--yolo", "--allow-all-tools", "--no-auto-update", "--extra"],
        ),
        (gemini, ["--flag"], ["--yolo", "--flag"]),
        (opencode, ["--inspect"], ["--inspect"]),
        (
            pi,
            ["--agent", "coder"],
            ["--agent", "coder", "--tools", "read,bash,edit,write,grep,find,ls"],
        ),
        (kiro, ["--ai"], ["--ai"]),
        (claude, ["--session"], ["--dangerously-skip-permissions", "--session"]),
    ],
)
def test_ai_launchers_use_resolved_executable_path_from_require_commands(
    monkeypatch,
    tmp_path,
    module,
    args,
    expected_tail,
):
    """
    @brief Validate CLI launchers execute the resolved executable path.
    @details Mocks `require_commands` to return a Windows-style resolved path
      and verifies launcher execution uses that resolved token as argv[0].
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @param module {module} CLI launcher module under test.
    @param args {list[str]} Pass-through command arguments.
    @param expected_tail {list[str]} Expected fixed and forwarded argument tail.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-055, REQ-056, REQ-064, REQ-068
    """

    observed = {}
    resolved_exec = r"C:\Tools\resolved-tool.cmd"

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=27)

    monkeypatch.setattr(module, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(module, "require_commands", lambda *_cmds: resolved_exec)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)
    if module is claude:
        monkeypatch.setattr(module.Path, "home", lambda: tmp_path)

    result = module.run(args)

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
