"""
@brief Validate `req` command target selection and external argv generation.
@details Verifies default/current-directory mode, `--dirs`, `--recursive`,
  mutual exclusion handling, and runtime-configured provider/static-check
  argument injection while preserving hardcoded non-overridable args.
@satisfies TST-010, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import shell_scripts.commands.req_cmd as req_cmd


def _create_dir(path: Path) -> None:
    """@brief Ensure directory exists for test fixture preparation.

    @details Creates target directory and parents using deterministic
    filesystem operation.
    @param path {Path} Directory path to create.
    @return {None} Side effects only.
    """

    path.mkdir(parents=True, exist_ok=True)


def test_req_default_targets_current_directory(monkeypatch, tmp_path):
    """
    @brief Validate default target-selection mode.
    @details Runs command without selectors and asserts exactly one subprocess
      execution with `--base` pointing to current working directory.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-049, REQ-051
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
    monkeypatch.setattr(req_cmd, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        req_cmd,
        "get_req_profile",
        lambda: (["claude:prompts"], ["Python=Ruff"]),
    )

    result = req_cmd.run([])

    assert result == 0
    assert len(observed) == 1
    assert observed[0][0] == "req"
    assert observed[0][observed[0].index("--base") + 1] == str(tmp_path)


def test_req_dirs_targets_only_first_level_children(monkeypatch, tmp_path):
    """
    @brief Validate `--dirs` selection semantics.
    @details Creates first-level and nested directories, runs `--dirs`, and
      asserts only non-hidden first-level directories are targeted.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-052
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
    monkeypatch.setattr(req_cmd.subprocess, "run", _fake_run)
    monkeypatch.setattr(req_cmd, "get_req_profile", lambda: ([], []))

    result = req_cmd.run(["--dirs"])

    assert result == 0
    assert observed_bases == [str(tmp_path / "a"), str(tmp_path / "b")]


def test_req_recursive_targets_descendants_only(monkeypatch, tmp_path):
    """
    @brief Validate `--recursive` selection semantics.
    @details Creates multi-level descendants and hidden paths, runs
      `--recursive`, and asserts all non-hidden descendants are targeted while
      current directory is excluded.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-053
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

    assert result == 0
    assert observed_bases == [
        str(tmp_path / "a"),
        str(tmp_path / "a" / "nested"),
        str(tmp_path / "b"),
    ]


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
    @satisfies TST-010, REQ-048
    """

    opencode_prompt = tmp_path / ".opencode" / "prompt"
    opencode_command = tmp_path / ".opencode" / "command"
    opencode_prompt.mkdir(parents=True, exist_ok=True)
    opencode_command.mkdir(parents=True, exist_ok=True)

    req_cmd._prepare_target_directory(tmp_path)

    assert not opencode_prompt.exists()
    assert not opencode_command.exists()
