"""
@brief Validate tests/venv command virtual-environment lifecycle behavior.
@details Verifies `.venv` creation/recreation and conditional requirements
  installation plus pytest invocation contract with `.venv/bin/python3` and
  `PYTHONPATH` prefixing.
@satisfies TST-008, REQ-036, REQ-037, REQ-038
@return {None} Pytest module scope.
"""

import subprocess
import sys

import shell_scripts.commands.tests_cmd as tests_cmd
import shell_scripts.commands.venv_cmd as venv_cmd


def test_tests_cmd_creates_venv_and_installs_requirements_when_present(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate tests command setup path with requirements file.
    @details Forces missing `.venv`, provides `requirements.txt`, intercepts
      subprocess calls, and verifies venv creation, pip install, and pytest
      execution through `.venv/bin/python3` with `PYTHONPATH` prefixed by `src`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-008, REQ-036, REQ-037
    """

    (tmp_path / "requirements.txt").write_text("pytest\n")
    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for tests command setup path.
        @details Captures execution payload and returns successful completion.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[None]} Successful completion object.
        """

        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(tests_cmd, "require_project_root", lambda: tmp_path)
    monkeypatch.setattr(tests_cmd.subprocess, "run", _fake_run)

    result = tests_cmd.run(["-q"])

    assert result == 0
    assert calls[0][0] == [sys.executable, "-m", "venv", str(tmp_path / ".venv")]
    assert calls[1][0] == [
        str(tmp_path / ".venv" / "bin" / "pip"),
        "install",
        "-r",
        str(tmp_path / "requirements.txt"),
    ]
    assert calls[-1][0] == [
        str(tmp_path / ".venv" / "bin" / "python3"),
        "-m",
        "pytest",
        "-q",
    ]
    env = calls[-1][1]["env"]
    assert env["PYTHONPATH"].startswith(str(tmp_path / "src") + ":")


def test_tests_cmd_skips_requirements_install_when_absent(monkeypatch, tmp_path):
    """
    @brief Validate tests command setup path without requirements file.
    @details Forces missing `.venv` and absent `requirements.txt`, intercepts
      subprocess calls, and verifies no pip-install call is issued.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-008, REQ-037
    """

    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for tests command without requirements.
        @details Captures execution payload and returns successful completion.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[None]} Successful completion object.
        """

        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(tests_cmd, "require_project_root", lambda: tmp_path)
    monkeypatch.setattr(tests_cmd.subprocess, "run", _fake_run)

    result = tests_cmd.run([])

    assert result == 0
    joined = [" ".join(cmd) for cmd, _kwargs in calls]
    assert not any("pip install -r" in value for value in joined)
    assert any(
        value.startswith(f"{tmp_path / '.venv' / 'bin' / 'python3'} -m pytest")
        for value in joined
    )


def test_venv_cmd_recreates_existing_venv_and_installs_requirements(
    monkeypatch,
    tmp_path,
):
    """
    @brief Validate venv command recreation with requirements installation.
    @details Precreates `.venv`, provides `requirements.txt`, intercepts
      deletion and subprocess boundaries, and verifies recreate + pip install.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-008, REQ-038
    """

    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (tmp_path / "requirements.txt").write_text("pytest\n")
    removed = []
    calls = []

    def _fake_rmtree(path):
        """
        @brief Mock shutil.rmtree for venv recreation.
        @details Captures requested path removal.
        @param path {str | os.PathLike[str]} Directory path.
        @return {None} Captures side-effect only.
        """

        removed.append(path)

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for venv recreation path.
        @details Captures execution payload and returns successful completion.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[None]} Successful completion object.
        """

        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(venv_cmd, "require_project_root", lambda: tmp_path)
    monkeypatch.setattr(venv_cmd.shutil, "rmtree", _fake_rmtree)
    monkeypatch.setattr(venv_cmd.subprocess, "run", _fake_run)

    result = venv_cmd.run([])

    assert result == 0
    assert removed == [venv_dir]
    assert calls[0][0] == [sys.executable, "-m", "venv", str(venv_dir)]
    assert calls[1][0] == [
        str(venv_dir / "bin" / "pip"),
        "install",
        "-r",
        str(tmp_path / "requirements.txt"),
    ]


def test_venv_cmd_skips_pip_install_when_requirements_absent(monkeypatch, tmp_path):
    """
    @brief Validate venv command when requirements file is absent.
    @details Intercepts subprocess boundary and verifies venv creation occurs
      while pip-install step is skipped.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-008, REQ-038
    """

    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for venv creation without requirements.
        @details Captures execution payload and returns successful completion.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[None]} Successful completion object.
        """

        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(venv_cmd, "require_project_root", lambda: tmp_path)
    monkeypatch.setattr(venv_cmd.subprocess, "run", _fake_run)

    result = venv_cmd.run([])

    assert result == 0
    assert calls[0][0] == [sys.executable, "-m", "venv", str(tmp_path / ".venv")]
    joined = [" ".join(cmd) for cmd, _kwargs in calls]
    assert not any("pip install -r" in value for value in joined)
