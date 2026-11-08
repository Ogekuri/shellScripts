"""
@brief Validate PyPI-primary version sourcing, version reporting, and develop upgrade flows.
@details Verifies startup update checks against the PyPI JSON API, GitHub
  latest-release resolution, the three-line `--version` report, the PyPI
  default upgrade command, the `--upgrade --dev`/`--develop` GitHub-tagged
  upgrade command, develop-upgrade failure handling, and rejection of the
  develop selector without `--upgrade`. All HTTP and subprocess boundaries are
  monkeypatched; no real network, filesystem, clock, or randomness access.
  Level classification: Level 0 tests exercise single module functions;
  Level 1 tests exercise `core.main` dispatch with patched boundaries.
@satisfies TST-014, REQ-003, REQ-075, REQ-076, REQ-077, REQ-078, DES-018, DES-019, DES-020
@return {None} Pytest module scope.
"""

import json
import types
import urllib.error
from email.message import Message

import shell_scripts.core as core
from shell_scripts.config import get_default_runtime_config
import shell_scripts.version_check as version_check


class _FakeResponse:
    """
    @brief Deterministic URLcontext-manager response for urlopen fakes.
    @details Wraps a JSON payload and satisfies the `with` protocol used by
      `_fetch_json_payload`.
    @param payload {dict[str, object]} JSON object served by `read()`.
    """

    def __init__(self, payload):
        """
        @brief Store serialized payload.
        @param payload {dict[str, object]} JSON object to serve.
        @return {None} Constructor side effect only.
        """
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        """
        @brief Serve stored payload bytes.
        @return {bytes} UTF-8 encoded JSON document.
        """
        return self._payload

    def __enter__(self):
        """
        @brief Enter context manager.
        @return {_FakeResponse} Self reference.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        @brief Exit context manager without suppression.
        @param exc_type {type|None} Exception class.
        @param exc_value {Exception|None} Exception instance.
        @param traceback {object|None} Traceback object.
        @return {bool} Always `False`.
        """
        return False


def _patch_urlopen(monkeypatch, expected_url, payload):
    """
    @brief Install a deterministic urlopen fake for one expected URL.
    @details Captures the requested URL, serves `_FakeResponse(payload)`, and
      raises `AssertionError` for unexpected URLs.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param expected_url {str} URL the fake must accept.
    @param payload {dict[str, object]} JSON payload served by the fake.
    @return {None} Installs monkeypatch side effect.
    """

    def _fake_urlopen(request, timeout=None):
        """
        @brief Serve payload only for the expected URL.
        @param request {urllib.request.Request} Outgoing request object.
        @param timeout {int|None} Unused timeout parameter.
        @return {_FakeResponse} Deterministic response.
        @throws {AssertionError} When URL differs from expected.
        """
        assert request.full_url == expected_url, (
            f"unexpected request URL: {request.full_url}"
        )
        return _FakeResponse(payload)

    monkeypatch.setattr(version_check.urllib.request, "urlopen", _fake_urlopen)


def test_fetch_pypi_latest_version_extracts_info_version(monkeypatch):
    """
    @brief Validate PyPI latest-version resolution contract.
    @details Installs a deterministic urlopen fake for the PyPI JSON API and
      asserts the function returns field `info.version` unchanged.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-014, DES-018
    """
    _patch_urlopen(
        monkeypatch,
        version_check.PYPI_API_URL,
        {"info": {"version": "9.9.9"}},
    )

    result = version_check.fetch_pypi_latest_version("0.1.0")

    expected_output = "9.9.9"
    assert result == expected_output


def test_fetch_github_latest_release_returns_raw_tag(monkeypatch):
    """
    @brief Validate GitHub latest-release tag resolution contract.
    @details Installs a deterministic urlopen fake for the GitHub Releases API
      and asserts the function returns field `tag_name` with its `v` prefix.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-014, DES-019
    """
    _patch_urlopen(
        monkeypatch,
        version_check.GITHUB_API_URL,
        {"tag_name": "v1.2.3"},
    )

    result = version_check.fetch_github_latest_release("0.1.0")

    expected_output = "v1.2.3"
    assert result == expected_output


def test_check_for_updates_queries_pypi_and_applies_success_cooldown(
    monkeypatch,
    capsys,
):
    """
    @brief Validate startup update check against the PyPI registry.
    @details Forces the check gate, intercepts urlopen so only the PyPI JSON
      API is queried, intercepts cooldown persistence, and asserts the
      bright-green update line plus success cooldown duration.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, PRJ-004, DES-004, DES-018, REQ-060
    """
    monkeypatch.setattr(version_check, "_should_check", lambda force_check: True)
    monkeypatch.setattr(
        version_check.sys, "argv", ["shellscripts"]
    )
    _patch_urlopen(
        monkeypatch,
        version_check.PYPI_API_URL,
        {"info": {"version": "9.9.9"}},
    )
    observed_cooldowns = []
    monkeypatch.setattr(
        version_check,
        "_write_idle_config",
        lambda _ts, delay: observed_cooldowns.append(delay),
    )

    version_check.check_for_updates("0.1.0")
    captured = capsys.readouterr()

    expected_output = "Versione Disponibile: 9.9.9"
    assert expected_output in captured.out
    assert "Versione Installata: 0.1.0" in captured.out
    assert observed_cooldowns == [version_check.IDLE_DELAY]


def test_print_remote_latest_versions_prints_both_latest_lines(
    monkeypatch,
    capsys,
):
    """
    @brief Validate dual-source latest-version report lines.
    @details Patches both fetch helpers and asserts the exact ordered report
      lines with the GitHub tag prefix stripped.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-075
    """
    monkeypatch.setattr(
        version_check, "fetch_pypi_latest_version", lambda _version: "1.2.3"
    )
    monkeypatch.setattr(
        version_check, "fetch_github_latest_release", lambda _version: "v4.5.6"
    )

    version_check.print_remote_latest_versions("0.1.0")
    captured = capsys.readouterr()

    expected_output = ["PyPI latest: 1.2.3", "GitHub latest: 4.5.6"]
    assert captured.out.splitlines() == expected_output


def test_print_remote_latest_versions_reports_failed_source_and_continues(
    monkeypatch,
    capsys,
):
    """
    @brief Validate per-source error reporting during version report.
    @details Forces the PyPI lookup to raise a non-HTTP exception and asserts
      the bright-red `PyPI latest: unknown (<reason>)` failure line while the
      GitHub line is still emitted.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-084, DES-020
    """

    def _raise_url_error(_version):
        """
        @brief Simulate PyPI connection failure.
        @param _version {str} Unused installed version.
        @return {None} Always raises.
        @throws {urllib.error.URLError} Deterministic failure.
        """
        raise urllib.error.URLError("pypi unreachable")

    monkeypatch.setattr(version_check, "fetch_pypi_latest_version", _raise_url_error)
    monkeypatch.setattr(
        version_check, "fetch_github_latest_release", lambda _version: "v0.1.0"
    )

    version_check.print_remote_latest_versions("0.1.0")
    captured = capsys.readouterr()

    expected_output = "PyPI latest: unknown (URLError: <urlopen error pypi unreachable>)"
    assert expected_output in captured.out
    assert "PyPI latest check failed" not in captured.out
    assert "GitHub latest: 0.1.0" in captured.out


def test_print_remote_latest_versions_reports_github_http_404(
    monkeypatch,
    capsys,
):
    """
    @brief Validate GitHub HTTP failure rendering during version report.
    @details Forces the GitHub lookup to raise an HTTP 404 error and asserts
      the bright-red `GitHub latest: unknown (HTTP 404)` failure line while
      the PyPI line is still emitted.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-084, DES-020
    """

    def _raise_http_404(_version):
        """
        @brief Simulate GitHub API HTTP 404 failure.
        @param _version {str} Unused installed version.
        @return {None} Always raises.
        @throws {urllib.error.HTTPError} Deterministic HTTP failure.
        """
        raise urllib.error.HTTPError(
            version_check.GITHUB_API_URL, 404, "Not Found", Message(), None
        )

    monkeypatch.setattr(
        version_check, "fetch_pypi_latest_version", lambda _version: "0.1.0"
    )
    monkeypatch.setattr(
        version_check, "fetch_github_latest_release", _raise_http_404
    )

    version_check.print_remote_latest_versions("0.1.0")
    captured = capsys.readouterr()

    expected_output = "GitHub latest: unknown (HTTP 404)"
    assert expected_output in captured.out
    assert "GitHub latest check failed" not in captured.out
    assert "PyPI latest: 0.1.0" in captured.out


def test_main_version_prints_installed_pypi_and_github_lines(
    monkeypatch,
    capsys,
):
    """
    @brief Validate the exact three-line `--version` report.
    @details Suppresses startup update checks, patches remote fetch helpers,
      and asserts the installed version line followed by the PyPI and GitHub
      latest lines in order.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-003, REQ-075
    """
    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(
        version_check, "fetch_pypi_latest_version", lambda _version: "2.0.0"
    )
    monkeypatch.setattr(
        version_check, "fetch_github_latest_release", lambda _version: "v3.0.0"
    )
    monkeypatch.setattr(core.sys, "argv", ["shellscripts", "--version"])

    result = core.main()
    captured = capsys.readouterr()

    expected_output = [
        core.__version__,
        "PyPI latest: 2.0.0",
        "GitHub latest: 3.0.0",
    ]
    assert result == 0
    assert captured.out.splitlines()[:3] == expected_output


def test_do_upgrade_default_resolves_pypi_command(monkeypatch):
    """
    @brief Validate the PyPI default upgrade command contract.
    @details Forces the Linux path, keeps the real runtime-config resolution,
      and intercepts subprocess invocation to assert the configured default
      command installs the package from PyPI.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-004
    """
    observed = {}

    def _fake_run(command, shell=False):
        """
        @brief Mock subprocess.run for the upgrade path.
        @param command {str} Shell command string.
        @param shell {bool} Shell execution selector.
        @return {types.SimpleNamespace} Object with returncode field.
        """
        observed["command"] = command
        observed["shell"] = shell
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(core, "is_linux", lambda: True)
    monkeypatch.setattr(
        core, "require_shell_command_executables", lambda command: None
    )
    monkeypatch.setattr(
        core,
        "get_management_command",
        lambda name: get_default_runtime_config()["management"][name],
    )
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_upgrade()

    expected_output = "uv tool install shellscripts --force"
    assert result == 0
    assert observed["shell"] is True
    assert observed["command"] == expected_output


def test_do_upgrade_develop_upgrades_from_latest_github_tag(monkeypatch):
    """
    @brief Validate the GitHub-tagged develop upgrade command contract.
    @details Patches the latest-tag resolution and intercepts subprocess
      invocation to assert the tag-pinned GitHub install command and code
      propagation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-076, DES-019
    """
    observed = {}

    def _fake_run(command, shell=False):
        """
        @brief Mock subprocess.run for the develop upgrade path.
        @param command {str} Shell command string.
        @param shell {bool} Shell execution selector.
        @return {types.SimpleNamespace} Object with returncode field.
        """
        observed["command"] = command
        observed["shell"] = shell
        return types.SimpleNamespace(returncode=5)

    monkeypatch.setattr(core, "is_linux", lambda: True)
    monkeypatch.setattr(
        core, "require_shell_command_executables", lambda command: None
    )
    monkeypatch.setattr(
        core,
        "get_management_command",
        lambda name: get_default_runtime_config()["management"][name],
    )
    monkeypatch.setattr(
        core, "fetch_github_latest_release", lambda _version: "v1.2.3"
    )
    monkeypatch.setattr(core.subprocess, "run", _fake_run)

    result = core.do_upgrade(develop=True)

    expected_output = (
        "uv tool install shellscripts --force "
        "--from git+https://github.com/Ogekuri/shellScripts.git@v1.2.3"
    )
    assert result == 5
    assert observed["shell"] is True
    assert observed["command"] == expected_output


def test_do_upgrade_develop_fails_when_tag_resolution_fails(
    monkeypatch,
    capsys,
):
    """
    @brief Validate develop-upgrade failure handling.
    @details Forces tag resolution to raise a connection error and asserts
      return code `1` plus a bright-red error line without subprocess
      invocation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-078
    """

    def _raise_url_error(_version):
        """
        @brief Simulate GitHub latest-release failure.
        @param _version {str} Unused installed version.
        @return {None} Always raises.
        @throws {urllib.error.URLError} Deterministic failure.
        """
        raise urllib.error.URLError("github unreachable")

    def _fail_run(_command, **_kwargs):
        """
        @brief Fail the test if subprocess is reached.
        @param _command {str} Unused command.
        @param _kwargs {dict} Unused keyword arguments.
        @return {None} Always raises.
        @throws {AssertionError} Unconditional.
        """
        raise AssertionError("subprocess must not run when tag resolution fails")

    monkeypatch.setattr(core, "is_linux", lambda: True)
    monkeypatch.setattr(core, "fetch_github_latest_release", _raise_url_error)
    monkeypatch.setattr(core.subprocess, "run", _fail_run)

    result = core.do_upgrade(develop=True)
    captured = capsys.readouterr()

    assert result == 1
    assert "GitHub latest release resolution failed" in captured.err


def test_main_rejects_develop_flag_without_upgrade(monkeypatch, capsys):
    """
    @brief Validate rejection of bare develop selector flags.
    @details Injects `--develop` and `--dev` as first argument and asserts
      return code `1` plus an explanatory error line for both spellings.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-077
    """
    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core, "print_remote_latest_versions", lambda _version: None)

    for flag in ("--develop", "--dev"):
        monkeypatch.setattr(core.sys, "argv", ["shellscripts", flag])
        result = core.main()
        captured = capsys.readouterr()

        assert result == 1, f"flag {flag} must be rejected"
        assert "must be used together with --upgrade" in captured.err


def test_main_upgrade_accepts_develop_aliases(monkeypatch):
    """
    @brief Validate develop-selector aliases on the upgrade flag.
    @details Replaces `do_upgrade` with a recorder and asserts the develop
      selector is `True` for both `--dev` and `--develop` spellings.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-014, REQ-076
    """
    observed_calls = []

    def _record_upgrade(develop=False):
        """
        @brief Record develop selector values.
        @param develop {bool} Develop selector flag.
        @return {int} Deterministic success code.
        """
        observed_calls.append(develop)
        return 0

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core, "print_remote_latest_versions", lambda _version: None)
    monkeypatch.setattr(core, "do_upgrade", _record_upgrade)

    for flag in ("--dev", "--develop"):
        monkeypatch.setattr(
            core.sys, "argv", ["shellscripts", "--upgrade", flag]
        )
        result = core.main()
        assert result == 0

    expected_output = [True, True]
    assert observed_calls == expected_output
