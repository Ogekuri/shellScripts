"""
@brief Validate `req` command target selection and external argv generation.
@details Verifies default/current-directory mode, `--dirs`, `--recursive`,
  mutual exclusion handling, cleanup evidence emission, and
  runtime-configured provider/static-check argument injection while preserving
  hardcoded non-overridable args.
@satisfies TST-010, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053,
  REQ-054, REQ-062, REQ-063, REQ-070, REQ-071
@return {None} Pytest module scope.
"""

import types
from pathlib import Path

import shell_scripts.commands.req_cmd as req_cmd


def _create_dir(path: Path) -> None:
    """@brief Ensure directory exists for test fixture preparation.

    @details Creates target directory and parents using deterministic
    filesystem operation.
    @param path {Path} Directory path to create.
    @return {None} Side effects only.
    """

    path.mkdir(parents=True, exist_ok=True)


def test_req_default_targets_current_directory(monkeypatch, tmp_path, capsys):
    """
    @brief Validate default target-selection mode.
    @details Runs command without selectors and asserts exactly one subprocess
      execution with `--base` pointing to current working directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-049, REQ-051, REQ-062
    """

    observed: list[list[str]] = []

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for req dispatch.
        @details Captures argv vector and returns deterministic success.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        observed.append(command)
        assert check is True
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    _create_dir(tmp_path / ".opencode" / "prompt")
    codex_prompt_file = tmp_path / ".codex" / "prompts"
    codex_prompt_file.parent.mkdir(parents=True, exist_ok=True)
    codex_prompt_file.write_text("prompt-body", encoding="utf-8")
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd, "_is_git_repository_root", lambda _path: True)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        req_cmd,
        "get_req_profile",
        lambda: (["claude:prompts"], ["Python=Ruff"]),
    )

    result = req_cmd.run([])
    output = capsys.readouterr().out

    assert result == 0
    assert len(observed) == 1
    assert observed[0][0] == "req"
    assert observed[0][observed[0].index("--base") + 1] == str(tmp_path)
    assert f"Cleanup target: {tmp_path}" in output
    assert f"clean | deleted | dir | {tmp_path / '.opencode' / 'prompt'}" in output
    assert f"clean | deleted | file | {codex_prompt_file}" in output
    assert f"clean | skip | missing | {tmp_path / '.gemini' / 'commands'}" in output


def test_req_dirs_targets_only_first_level_children(monkeypatch, tmp_path, capsys):
    """
    @brief Validate `--dirs` selection semantics.
    @details Creates first-level and nested directories, runs `--dirs`, and
      asserts only non-hidden first-level directories are targeted.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-052, REQ-062
    """

    _create_dir(tmp_path / "a")
    _create_dir(tmp_path / "b")
    _create_dir(tmp_path / "a" / "nested")
    _create_dir(tmp_path / ".hidden")

    observed_bases: list[str] = []

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for --dirs path.
        @details Captures `--base` values for later assertions.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del check
        observed_bases.append(command[command.index("--base") + 1])
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd, "_is_git_repository_root", lambda _path: True)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "get_req_profile", lambda: ([], []))

    result = req_cmd.run(["--dirs"])
    output = capsys.readouterr().out

    assert result == 0
    assert observed_bases == [str(tmp_path / "a"), str(tmp_path / "b")]
    assert f"Cleanup target: {tmp_path / 'a'}" in output
    assert f"Cleanup target: {tmp_path / 'b'}" in output


def test_req_recursive_targets_descendants_only(monkeypatch, tmp_path, capsys):
    """
    @brief Validate `--recursive` selection semantics.
    @details Creates multi-level descendants and hidden paths, runs
      `--recursive`, and asserts all non-hidden descendants are targeted while
      current directory is excluded.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-053, REQ-062
    """

    _create_dir(tmp_path / "a")
    _create_dir(tmp_path / "a" / "nested")
    _create_dir(tmp_path / "b")
    _create_dir(tmp_path / ".hidden" / "n")

    observed_bases: list[str] = []

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for recursive path.
        @details Captures `--base` values for later assertions.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del check
        observed_bases.append(command[command.index("--base") + 1])
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "get_req_profile", lambda: ([], []))

    result = req_cmd.run(["--recursive"])
    output = capsys.readouterr().out

    assert result == 0
    assert observed_bases == [
        str(tmp_path / "a"),
        str(tmp_path / "a" / "nested"),
        str(tmp_path / "b"),
    ]
    assert f"Cleanup target: {tmp_path / 'a'}" in output
    assert f"Cleanup target: {tmp_path / 'a' / 'nested'}" in output
    assert f"Cleanup target: {tmp_path / 'b'}" in output


def test_req_rejects_dirs_and_recursive_together(monkeypatch):
    """
    @brief Validate mutual-exclusion option guard.
    @details Executes command with both selectors enabled and asserts return
      code `1` without subprocess invocation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-054
    """

    observed = {"calls": 0}

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for mutual-exclusion test.
        @details Tracks accidental invocations.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del command, check
        observed["calls"] += 1
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)

    result = req_cmd.run(["--dirs", "--recursive"])

    assert result == 1
    assert observed["calls"] == 0


def test_req_returns_error_code_when_external_req_fails(monkeypatch, tmp_path):
    """
    @brief Validate subprocess-failure propagation without traceback.
    @details Simulates external `req` failure and asserts command returns the
      subprocess exit code instead of raising `CalledProcessError`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-049, REQ-051
    """

    observed = {"error": ""}

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for external req failure simulation.
        @details Raises `CalledProcessError` with deterministic exit code.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Unused because exception is raised.
        @exception {subprocess.CalledProcessError} Always raised for test flow.
        """

        raise req_cmd.subprocess.CalledProcessError(returncode=3, cmd=command)

    def _fake_print_error(message):
        """
        @brief Capture error output from req command.
        @details Stores the emitted error message for strict assertions.
        @param message {str} Error message emitted by command.
        @return {None} Side effects only.
        """

        observed["error"] = message

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd, "_is_git_repository_root", lambda _path: True)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "print_error", _fake_print_error)
    monkeypatch.setattr(req_cmd, "get_req_profile", lambda: ([], []))

    result = req_cmd.run([])

    assert result == 3
    assert "exit code 3" in observed["error"]


def test_req_builds_hardcoded_and_configurable_args(monkeypatch, tmp_path):
    """
    @brief Validate req argv assembly contract.
    @details Asserts hardcoded base args are always present and provider/static
      check lists are appended from runtime profile.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-049, REQ-050
    """

    observed: list[list[str]] = []

    def _fake_run(command, check):
        """
        @brief Mock subprocess.run for argument validation.
        @details Captures argv for strict token checks.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del check
        observed.append(command)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd, "_is_git_repository_root", lambda _path: True)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        req_cmd,
        "get_req_profile",
        lambda: (["a:b", "c:d"], ["Python=Ruff", "JavaScript=Command,node,--check"]),
    )

    result = req_cmd.run([])

    assert result == 0
    command = observed[0]
    assert "--docs-dir" in command
    assert "--guidelines-dir" in command
    assert command.count("--src-dir") == 3
    assert "--tests-dir" in command
    assert command.count("--provider") == 2
    assert command.count("--enable-static-check") == 2
    assert "--upgrade-guidelines" in command


def test_req_prepare_target_directory_cleans_opencode_prompt_path(tmp_path):
    """
    @brief Validate OpenCode prompt cleanup target path.
    @details Creates `.opencode/prompt` and `.opencode/command` directories,
      runs target preparation, and asserts both directories are removed by
      predefined cleanup list semantics.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-048, REQ-062, REQ-063
    """

    opencode_prompt = tmp_path / ".opencode" / "prompt"
    opencode_command = tmp_path / ".opencode" / "command"
    opencode_prompt.mkdir(parents=True, exist_ok=True)
    opencode_command.mkdir(parents=True, exist_ok=True)

    evidence = req_cmd._prepare_target_directory(tmp_path)

    assert not opencode_prompt.exists()
    assert not opencode_command.exists()
    assert ("deleted", "dir", opencode_prompt) in evidence
    assert ("deleted", "dir", opencode_command) in evidence


def test_req_prepare_target_directory_reports_deleted_file_and_skip(tmp_path):
    """
    @brief Validate cleanup evidence for file deletion and missing-path skip.
    @details Creates one cleanup file entry, leaves another predefined cleanup
      path absent, runs target preparation, and asserts evidence records `file`
      deletion and `skip` for the missing path.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-048, REQ-062, REQ-063
    """

    cleanup_file = tmp_path / ".codex" / "prompts"
    cleanup_file.parent.mkdir(parents=True, exist_ok=True)
    cleanup_file.write_text("prompt-body", encoding="utf-8")
    missing_path = tmp_path / ".kiro" / "skills"

    evidence = req_cmd._prepare_target_directory(tmp_path)

    assert not cleanup_file.exists()
    assert ("deleted", "file", cleanup_file) in evidence
    assert ("skip", "missing", missing_path) in evidence


def test_req_current_directory_skips_when_not_git_root(
    monkeypatch,
    tmp_path,
    capsys,
):
    """
    @brief Validate skip flow for non-root current directory.
    @details Runs default mode with Git-root predicate returning `False` and
      asserts command prints one skip evidence line containing `skippata` while
      avoiding cleanup and external req execution.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-070
    """

    observed = {"prepare_calls": 0, "run_calls": 0}

    def _fake_prepare(_target_dir: Path):
        """
        @brief Track unexpected cleanup preparation invocation.
        @details Increments local counter when called.
        @param _target_dir {Path} Unused target path.
        @return {list[tuple[str, str, Path]]} Empty cleanup evidence list.
        """

        observed["prepare_calls"] += 1
        return []

    def _fake_run(command, check):
        """
        @brief Track unexpected external req invocation.
        @details Increments local counter and returns deterministic success.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del command, check
        observed["run_calls"] += 1
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd, "_is_git_repository_root", lambda _path: False)
    monkeypatch.setattr(req_cmd, "_prepare_target_directory", _fake_prepare)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)

    result = req_cmd.run([])
    output = capsys.readouterr().out

    assert result == 0
    assert observed["prepare_calls"] == 0
    assert observed["run_calls"] == 0
    assert "install | skip |" in output
    assert "skippata" in output
    assert str(tmp_path) in output


def test_req_dirs_skips_non_root_directories_only(monkeypatch, tmp_path, capsys):
    """
    @brief Validate `--dirs` selective skip and continue behavior.
    @details Creates two first-level directories, marks only one as Git root,
      and asserts external req executes only for eligible directory while
      skipped directory emits one skip evidence line containing `skippata`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-071
    """

    git_root_dir = tmp_path / "a"
    skipped_dir = tmp_path / "b"
    _create_dir(git_root_dir)
    _create_dir(skipped_dir)
    observed_bases: list[str] = []

    def _fake_run(command, check):
        """
        @brief Capture executed req base paths in mixed-skip flow.
        @details Records `--base` argument of external req invocations.
        @param command {list[str]} Command argv vector.
        @param check {bool} Subprocess check flag.
        @return {types.SimpleNamespace} Deterministic return code object.
        """

        del check
        observed_bases.append(command[command.index("--base") + 1])
        return types.SimpleNamespace(returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(
        req_cmd,
        "_is_git_repository_root",
        lambda path: path == git_root_dir,
    )
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "get_req_profile", lambda: ([], []))

    result = req_cmd.run(["--dirs"])
    output = capsys.readouterr().out

    assert result == 0
    assert observed_bases == [str(git_root_dir)]
    assert f"install | skip | {skipped_dir}" in output
    assert "skippata" in output
