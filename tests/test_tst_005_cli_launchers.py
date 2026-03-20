"""
@brief Validate CLI launcher command wrappers.
@details Verifies executable paths, argument vectors, project-root append
  behavior, CODEX_HOME environment setup, and codex auth symlink guard across
  cli-* and editor commands.
@satisfies TST-005, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019,
  REQ-020, REQ-021, REQ-043, REQ-044
@return {None} Pytest module scope.
"""

from pathlib import Path

import shell_scripts.commands.cli_claude as cli_claude
import shell_scripts.commands.cli_codex as cli_codex
import shell_scripts.commands.cli_copilot as cli_copilot
import shell_scripts.commands.cli_gemini as cli_gemini
import shell_scripts.commands.cli_kiro as cli_kiro
import shell_scripts.commands.cli_opencode as cli_opencode
import shell_scripts.commands.vscode_cmd as vscode_cmd
import shell_scripts.commands.vsinsider_cmd as vsinsider_cmd


def test_cli_codex_creates_auth_symlink_sets_codex_home_and_executes_expected_command(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate cli-codex creation path contract.
    @details Stubs project-root resolution and exec boundary, then validates
      auth-symlink creation, creation-message emission, CODEX_HOME assignment,
      and command vector.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-043, REQ-044
    """

    project_root = tmp_path / "project-a"
    fake_home = tmp_path / "home-a"
    project_root.mkdir(parents=True)
    fake_home.mkdir(parents=True)
    observed = {}
    observed_info = []

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-codex test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    def _fake_print_info(message):
        """
        @brief Mock informational logger for symlink creation path.
        @details Captures emitted informational message for assertion.
        @param message {str} Info text emitted by command implementation.
        @return {None} Captures side-effect only.
        """

        observed_info.append(message)

    monkeypatch.setattr(cli_codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(cli_codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(cli_codex, "print_info", _fake_print_info)
    monkeypatch.setattr(cli_codex.os, "execvp", _fake_execvp)

    try:
        cli_codex.run(["--x"])
    except SystemExit as exc:
        assert exc.code == 0

    expected_link = project_root / ".codex" / "auth.json"
    expected_target = fake_home / ".codex" / "auth.json"
    assert expected_link.is_symlink()
    assert expected_link.resolve(strict=False) == expected_target.resolve(strict=False)
    assert observed_info == [f"Created symlink: {expected_link} -> {expected_target}"]
    assert cli_codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["executable"] == "/usr/bin/codex"
    assert observed["args"] == ["/usr/bin/codex", "--yolo", "--x"]


def test_cli_codex_keeps_existing_auth_symlink_without_creation_message(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate cli-codex no-op path for compliant auth symlink.
    @details Precreates compliant project auth symlink and verifies command
      does not emit creation info while preserving execution contract.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-014, REQ-043, REQ-044
    """

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

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-codex no-op symlink test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    def _fake_print_info(message):
        """
        @brief Mock informational logger for no-op path assertion.
        @details Captures messages to verify creation log suppression.
        @param message {str} Info text emitted by command implementation.
        @return {None} Captures side-effect only.
        """

        observed_info.append(message)

    monkeypatch.setattr(cli_codex, "require_project_root", lambda: project_root)
    monkeypatch.setattr(cli_codex.Path, "home", lambda: fake_home)
    monkeypatch.setattr(cli_codex, "print_info", _fake_print_info)
    monkeypatch.setattr(cli_codex.os, "execvp", _fake_execvp)

    try:
        cli_codex.run(["--z"])
    except SystemExit as exc:
        assert exc.code == 0

    assert expected_link.is_symlink()
    assert expected_link.resolve(strict=False) == expected_target.resolve(strict=False)
    assert observed_info == []
    assert cli_codex.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["executable"] == "/usr/bin/codex"
    assert observed["args"] == ["/usr/bin/codex", "--yolo", "--z"]


def test_cli_copilot_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-copilot execution contract.
    @details Stubs project-root guard and exec boundary to assert command
      vector.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-015
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-copilot test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(cli_copilot, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_copilot.os, "execvp", _fake_execvp)

    try:
        cli_copilot.run(["--extra"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "/usr/bin/copilot"
    assert observed["args"] == [
        "/usr/bin/copilot",
        "--yolo",
        "--allow-all-tools",
        "--extra",
    ]


def test_cli_gemini_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-gemini execution contract.
    @details Stubs project-root guard and exec boundary to assert command
      vector.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-016
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-gemini test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(cli_gemini, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_gemini.os, "execvp", _fake_execvp)

    try:
        cli_gemini.run(["--flag"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "/usr/bin/gemini"
    assert observed["args"] == ["/usr/bin/gemini", "--yolo", "--flag"]


def test_cli_claude_executes_expected_command(monkeypatch, tmp_path):
    """
    @brief Validate cli-claude execution contract.
    @details Redirects home directory to deterministic path and asserts command
      vector includes expected Claude binary and safety flag.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-017
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-claude test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(cli_claude, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_claude.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(cli_claude.os, "execvp", _fake_execvp)

    try:
        cli_claude.run(["--session"])
    except SystemExit as exc:
        assert exc.code == 0

    expected_bin = str(tmp_path / ".claude" / "bin" / "claude")
    assert observed["executable"] == expected_bin
    assert observed["args"] == [
        expected_bin,
        "--dangerously-skip-permissions",
        "--session",
    ]


def test_cli_opencode_executes_expected_command(monkeypatch):
    """
    @brief Validate cli-opencode execution contract.
    @details Stubs project-root guard and exec boundary to assert command
      vector.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-018
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-opencode test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(cli_opencode, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_opencode.os, "execvp", _fake_execvp)

    try:
        cli_opencode.run(["--inspect"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "/usr/bin/opencode"
    assert observed["args"] == ["/usr/bin/opencode", "--inspect"]


def test_cli_kiro_executes_expected_command(monkeypatch, tmp_path):
    """
    @brief Validate cli-kiro execution contract.
    @details Redirects home directory to deterministic path and asserts command
      vector includes expected Kiro binary.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-019
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for cli-kiro test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(cli_kiro, "require_project_root", lambda: Path("/tmp/p"))
    monkeypatch.setattr(cli_kiro.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(cli_kiro.os, "execvp", _fake_execvp)

    try:
        cli_kiro.run(["--ai"])
    except SystemExit as exc:
        assert exc.code == 0

    expected_bin = str(tmp_path / ".local" / "bin" / "kiro-cli")
    assert observed["executable"] == expected_bin
    assert observed["args"] == [expected_bin, "--ai"]


def test_vscode_appends_project_path_and_sets_codex_home(monkeypatch):
    """
    @brief Validate vscode launcher behavior.
    @details Stubs project-root resolution, chdir, and exec boundary to assert
      CODEX_HOME assignment and final project-path argument placement.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-020, REQ-021
    """

    project_root = Path("/tmp/project-vscode")
    observed = {}

    def _fake_chdir(path):
        """
        @brief Mock os.chdir for vscode test.
        @details Captures requested working directory.
        @param path {str | os.PathLike[str]} Target directory path.
        @return {None} Captures side-effect only.
        """

        observed["chdir"] = path

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for vscode test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(vscode_cmd, "require_project_root", lambda: project_root)
    monkeypatch.setattr(vscode_cmd.os, "chdir", _fake_chdir)
    monkeypatch.setattr(vscode_cmd.os, "execvp", _fake_execvp)

    try:
        vscode_cmd.run(["--reuse-window"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["chdir"] == project_root
    assert vscode_cmd.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["executable"] == "/usr/share/code/bin/code"
    assert observed["args"][-1] == str(project_root)


def test_vsinsider_appends_project_path_and_sets_codex_home(monkeypatch):
    """
    @brief Validate VS Code Insiders launcher behavior.
    @details Stubs project-root resolution, chdir, and exec boundary to assert
      CODEX_HOME assignment and final project-path argument placement.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-005, REQ-020, REQ-021
    """

    project_root = Path("/tmp/project-vsinsider")
    observed = {}

    def _fake_chdir(path):
        """
        @brief Mock os.chdir for vsinsider test.
        @details Captures requested working directory.
        @param path {str | os.PathLike[str]} Target directory path.
        @return {None} Captures side-effect only.
        """

        observed["chdir"] = path

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for vsinsider test.
        @details Captures executable and argument vector; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(vsinsider_cmd, "require_project_root", lambda: project_root)
    monkeypatch.setattr(vsinsider_cmd.os, "chdir", _fake_chdir)
    monkeypatch.setattr(vsinsider_cmd.os, "execvp", _fake_execvp)

    try:
        vsinsider_cmd.run(["--new-window"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["chdir"] == project_root
    assert vsinsider_cmd.os.environ["CODEX_HOME"] == str(project_root / ".codex")
    assert observed["executable"] == "/usr/share/code-insiders/bin/code-insiders"
    assert observed["args"][-1] == str(project_root)
