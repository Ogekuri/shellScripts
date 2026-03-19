"""
@brief Validate Double Commander wrapper behavior and MIME dispatch.
@details Verifies missing-file return code path and category resolution using
  MIME and extension evidence with mocked process boundaries.
@satisfies TST-006, REQ-023, REQ-024
@return {None} Pytest module scope.
"""

import shell_scripts.commands._dc_common as dc_common
import shell_scripts.commands.dc_differ as dc_differ
import shell_scripts.commands.dc_editor as dc_editor
import shell_scripts.commands.dc_viewer as dc_viewer


def test_double_commander_wrappers_return_two_when_missing_file_argument():
    """
    @brief Validate missing-file-argument status code.
    @details Executes each double-commander wrapper with empty args and asserts
      mandated return code 2.
    @return {None} Assertions only.
    @satisfies TST-006, REQ-023
    """

    assert dc_differ.run([]) == 2
    assert dc_editor.run([]) == 2
    assert dc_viewer.run([]) == 2


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
