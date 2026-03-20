"""
@brief Validate generic diff/edit/view wrapper behavior and MIME dispatch.
@details Verifies missing-file return code path and category resolution using
  MIME and extension evidence with mocked process boundaries, including runtime
  dispatch-profile resolution.
@satisfies TST-006, REQ-023, REQ-024, REQ-045
@return {None} Pytest module scope.
"""

import shell_scripts.commands._dc_common as dc_common
import shell_scripts.commands.diff_cmd as diff_cmd
import shell_scripts.commands.edit_cmd as edit_cmd
import shell_scripts.commands.view_cmd as view_cmd
import shell_scripts.config as config


def test_diff_edit_view_wrappers_return_two_when_missing_file_argument():
    """
    @brief Validate missing-file-argument status code.
    @details Executes each diff/edit/view wrapper with empty args and asserts
      mandated return code 2.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-023
    """

    assert diff_cmd.run([]) == 2
    assert edit_cmd.run([]) == 2
    assert view_cmd.run([]) == 2


def test_categorize_uses_mime_and_extension_mapping(monkeypatch):
    """
    @brief Validate category resolution logic.
    @details Mocks MIME responses and file-existence checks to verify category
      mapping precedence across image, PDF, HTML, markdown, code, and text.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-024
    """

    monkeypatch.setattr(dc_common.os.path, "exists", lambda _p: True)

    monkeypatch.setattr(dc_common, "detect_mime", lambda _p: "image/png")
    assert dc_common.categorize("/tmp/a.png") == "image"

    monkeypatch.setattr(dc_common, "detect_mime", lambda _p: "application/pdf")
    assert dc_common.categorize("/tmp/a.any") == "pdf"

    monkeypatch.setattr(dc_common, "detect_mime", lambda _p: "text/html")
    assert dc_common.categorize("/tmp/a.any") == "html"

    monkeypatch.setattr(dc_common, "detect_mime", lambda _p: "text/plain")
    assert dc_common.categorize("/tmp/readme.md") == "markdown"
    assert dc_common.categorize("/tmp/source.py") == "code"
    assert dc_common.categorize("/tmp/notes.txt") == "text"


def test_dispatch_selects_category_specific_command(monkeypatch):
    """
    @brief Validate category-to-command dispatch routing.
    @details Mocks categorization, command lookup, and process replacement
      boundary to assert selected command receives file and extra args.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-024
    """

    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for dispatch test.
        @details Captures command payload and exits via SystemExit.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(dc_common, "categorize", lambda _path: "markdown")
    monkeypatch.setattr(dc_common.shutil, "which", lambda _cmd: "/usr/bin/fake")
    monkeypatch.setattr(dc_common.os, "execvp", _fake_execvp)

    category_cmds = {"markdown": ["typora"]}

    try:
        dc_common.dispatch(category_cmds, ["sushi"], "/tmp/readme.md", ["--line", "3"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "typora"
    assert observed["args"] == ["typora", "/tmp/readme.md", "--line", "3"]


def test_wrappers_use_runtime_dispatch_profiles(monkeypatch):
    """
    @brief Validate wrapper dispatch profile sourcing from runtime config.
    @details Monkeypatches profile resolvers for diff/edit/view wrappers and
      asserts `dispatch` receives the configured category/fallback payload.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-024, REQ-045
    """

    observed = []

    def _fake_dispatch(category_cmds, fallback_cmd, filepath, extra_args):
        """
        @brief Mock shared dispatch execution for wrappers.
        @details Captures payload and returns deterministic zero code.
        @param category_cmds {dict[str, list[str]]} Category command map.
        @param fallback_cmd {list[str]} Fallback command vector.
        @param filepath {str} Input path.
        @param extra_args {list[str]} Forwarded extra args.
        @return {int} Deterministic success code.
        """

        observed.append((category_cmds, fallback_cmd, filepath, extra_args))
        return 0

    monkeypatch.setattr(diff_cmd, "get_dispatch_profile", lambda _name: ({"text": ["difftool"]}, ["diff-fallback"]))
    monkeypatch.setattr(edit_cmd, "get_dispatch_profile", lambda _name: ({"text": ["edittool"]}, ["edit-fallback"]))
    monkeypatch.setattr(view_cmd, "get_dispatch_profile", lambda _name: ({"text": ["viewtool"]}, ["view-fallback"]))
    monkeypatch.setattr(diff_cmd, "dispatch", _fake_dispatch)
    monkeypatch.setattr(edit_cmd, "dispatch", _fake_dispatch)
    monkeypatch.setattr(view_cmd, "dispatch", _fake_dispatch)

    assert diff_cmd.run(["/tmp/a.txt", "--left"]) == 0
    assert edit_cmd.run(["/tmp/b.txt", "--line", "2"]) == 0
    assert view_cmd.run(["/tmp/c.txt"]) == 0

    assert observed[0] == ({"text": ["difftool"]}, ["diff-fallback"], "/tmp/a.txt", ["--left"])
    assert observed[1] == ({"text": ["edittool"]}, ["edit-fallback"], "/tmp/b.txt", ["--line", "2"])
    assert observed[2] == ({"text": ["viewtool"]}, ["view-fallback"], "/tmp/c.txt", [])



def test_diff_help_mentions_generic_command_name(capsys):
    """
    @brief Validate `diff` help naming.
    @details Ensures help output references the generic `diff` command token and
      excludes legacy naming tokens.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture fixture.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-023
    """

    diff_cmd.print_help("v")
    out = capsys.readouterr().out
    assert "diff options:" in out
    assert "double-commander" not in out


def test_edit_help_mentions_generic_command_name(capsys):
    """
    @brief Validate `edit` help naming.
    @details Ensures help output references the generic `edit` command token and
      excludes legacy naming tokens.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture fixture.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-023
    """

    edit_cmd.print_help("v")
    out = capsys.readouterr().out
    assert "edit options:" in out
    assert "double-commander" not in out


def test_view_help_mentions_generic_command_name(capsys):
    """
    @brief Validate `view` help naming.
    @details Ensures help output references the generic `view` command token and
      excludes legacy naming tokens.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture fixture.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-023
    """

    view_cmd.print_help("v")
    out = capsys.readouterr().out
    assert "view options:" in out
    assert "double-commander" not in out


def test_get_req_profile_uses_runtime_override_and_default_fallback(monkeypatch):
    """
    @brief Validate req profile resolution behavior.
    @details Injects runtime config with valid/invalid payloads and asserts
      `get_req_profile` returns runtime values when valid and hardcoded defaults
      when invalid.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-010, REQ-050
    """

    defaults = config.get_default_runtime_config()["req"]
    monkeypatch.setattr(
        config,
        "_runtime_config",
        {
            "req": {
                "providers": ["x:y"],
                "static_checks": ["Python=Ruff"],
            }
        },
    )

    providers, static_checks = config.get_req_profile()
    assert providers == ["x:y"]
    assert static_checks == ["Python=Ruff"]

    monkeypatch.setattr(
        config,
        "_runtime_config",
        {
            "req": {
                "providers": ["ok:value"],
                "static_checks": "invalid-type",
            }
        },
    )

    providers, static_checks = config.get_req_profile()
    assert providers == ["ok:value"]
    assert static_checks == defaults["static_checks"]
