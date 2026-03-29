"""
@brief Validate PDF command invocation contracts and page-range parsing.
@details Verifies qpdf/pdftk/gs/plakativ invocation sequences for covered PDF
  commands and validates accepted/rejected page-range grammar.
@satisfies TST-007, REQ-029, REQ-030, REQ-031, REQ-032, REQ-033, REQ-034,
  REQ-035
@return {None} Pytest module scope.
"""

import pathlib
import subprocess

import pytest

import shell_scripts.commands.pdf_crop as pdf_crop
import shell_scripts.commands.pdf_merge as pdf_merge
import shell_scripts.commands.pdf_split_by_format as pdf_split_by_format
import shell_scripts.commands.pdf_split_by_toc as pdf_split_by_toc
import shell_scripts.commands.pdf_tiler_090 as pdf_tiler_090
import shell_scripts.commands.pdf_tiler_100 as pdf_tiler_100
import shell_scripts.commands.pdf_toc_clean as pdf_toc_clean


def test_pdf_tiler_090_uses_a4_output_and_expected_filename(monkeypatch, tmp_path):
    """
    @brief Validate pdf-tiler-090 command vector.
    @details Mocks dependency checks and exec boundary, then asserts plakativ
      invocation includes A4 output and `<stem>_tiled-A4.pdf` naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-029
    """

    input_pdf = tmp_path / "doc.pdf"
    input_pdf.write_text("dummy")
    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for pdf-tiler-090.
        @details Captures executable and argv payload; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(pdf_tiler_090, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_tiler_090.os, "execvp", _fake_execvp)

    try:
        pdf_tiler_090.run([str(input_pdf)])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "plakativ"
    assert "--pagesize" in observed["args"]
    assert "A4" in observed["args"]
    assert str(tmp_path / "doc_tiled-A4.pdf") in observed["args"]


def test_pdf_tiler_100_uses_a4_output_and_expected_filename(monkeypatch, tmp_path):
    """
    @brief Validate pdf-tiler-100 command vector.
    @details Mocks dependency checks and exec boundary, then asserts plakativ
      invocation includes A4 output and `<stem>_tiled-A4.pdf` naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-029
    """

    input_pdf = tmp_path / "poster.pdf"
    input_pdf.write_text("dummy")
    observed = {}

    def _fake_execvp(executable, args):
        """
        @brief Mock os.execvp for pdf-tiler-100.
        @details Captures executable and argv payload; terminates flow.
        @param executable {str} Executable path.
        @param args {list[str]} Process argv vector.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        observed["executable"] = executable
        observed["args"] = args
        raise SystemExit(0)

    monkeypatch.setattr(pdf_tiler_100, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_tiler_100.os, "execvp", _fake_execvp)

    try:
        pdf_tiler_100.run([str(input_pdf)])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "plakativ"
    assert "--pagesize" in observed["args"]
    assert "A4" in observed["args"]
    assert str(tmp_path / "poster_tiled-A4.pdf") in observed["args"]


def test_pdf_merge_runs_qpdf_pdftk_sequence(monkeypatch, tmp_path):
    """
    @brief Validate pdf-merge subprocess sequence.
    @details Creates two dummy inputs, intercepts subprocess.run, provides
      deterministic dump metadata, and asserts qpdf/pdftk usage including final
      linearization.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-030
    """

    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.write_text("a")
    second.write_text("b")

    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for pdf-merge.
        @details Captures invocation list and writes deterministic intermediate
          files required by merge parser paths.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[str]} Successful completion object.
        """

        del kwargs
        calls.append(command)
        if "output" in command:
            output_index = command.index("output") + 1
            output_path = command[output_index]
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("NumberOfPages: 1\n")
                handle.write("BookmarkBegin\n")
                handle.write("BookmarkTitle: Chapter\n")
                handle.write("BookmarkLevel: 1\n")
                handle.write("BookmarkPageNumber: 1\n")
        elif command[0] == "qpdf" and command[1] == "--linearize":
            with open(command[-1], "w", encoding="utf-8") as handle:
                handle.write("linearized")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(pdf_merge, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_merge.subprocess, "run", _fake_run)

    output = tmp_path / "merged.pdf"
    result = pdf_merge.run(["-o", str(output), str(first), str(second)])

    assert result == 0
    assert any(cmd[0] == "qpdf" for cmd in calls)
    assert any(cmd[0] == "pdftk" for cmd in calls)
    assert any(cmd[:2] == ["qpdf", "--linearize"] for cmd in calls)


def test_pdf_split_by_toc_runs_required_tools(monkeypatch, tmp_path):
    """
    @brief Validate pdf-split-by-toc command sequence.
    @details Intercepts qpdf/pdftk execution and provides deterministic TOC
      data to assert split path executes required tools.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-031
    """

    input_pdf = tmp_path / "book.pdf"
    input_pdf.write_text("dummy")
    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for pdf-split-by-toc.
        @details Captures invocation list and writes deterministic TOC dump
          output when pdftk requests a dump-data file.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[str]} Successful completion object.
        """

        del kwargs
        calls.append(command)
        if command[0] == "pdftk" and "output" in command:
            output_path = command[command.index("output") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("NumberOfPages: 3\n")
                handle.write("BookmarkBegin\n")
                handle.write("BookmarkTitle: Intro\n")
                handle.write("BookmarkLevel: 1\n")
                handle.write("BookmarkPageNumber: 1\n")
                handle.write("BookmarkBegin\n")
                handle.write("BookmarkTitle: End\n")
                handle.write("BookmarkLevel: 1\n")
                handle.write("BookmarkPageNumber: 3\n")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(pdf_split_by_toc, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_split_by_toc.subprocess, "run", _fake_run)

    result = pdf_split_by_toc.run([str(input_pdf)])

    assert result == 0
    assert any(cmd[0] == "qpdf" for cmd in calls)
    assert any(cmd[0] == "pdftk" for cmd in calls)


def test_pdf_split_by_format_runs_required_tools(monkeypatch, tmp_path):
    """
    @brief Validate pdf-split-by-format command sequence.
    @details Intercepts helper functions and subprocess boundary to drive format
      transitions and assert qpdf/pdftk/pdfinfo workflow.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-032
    """

    input_pdf = tmp_path / "formats.pdf"
    input_pdf.write_text("dummy")
    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for pdf-split-by-format.
        @details Captures invocation list and returns successful completion.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[str]} Successful completion object.
        """

        del kwargs
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(pdf_split_by_format, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_split_by_format, "_get_total_pages", lambda _pdf: 3)
    monkeypatch.setattr(
        pdf_split_by_format,
        "_get_page_formats",
        lambda _pdf, _pages: ["A4", "A4", "A3"],
    )
    monkeypatch.setattr(pdf_split_by_format, "_has_toc", lambda _pdf: False)
    monkeypatch.setattr(pdf_split_by_format.subprocess, "run", _fake_run)

    result = pdf_split_by_format.run([str(input_pdf)])

    assert result == 0
    assert any(cmd[0] == "qpdf" for cmd in calls)


def test_pdf_toc_clean_generates_toc_clean_filename(monkeypatch, tmp_path):
    """
    @brief Validate pdf-toc-clean output naming and tool sequence.
    @details Intercepts subprocess boundary to provide deterministic pdftk dump
      data and qpdf linearization, then asserts `_toc-clean.pdf` output path.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-033
    """

    input_pdf = tmp_path / "toc.pdf"
    input_pdf.write_text("dummy")
    calls = []

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for pdf-toc-clean.
        @details Captures invocation list and provides deterministic dump-data
          output plus linearized artifact writes.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[str]} Successful completion object.
        """

        del kwargs
        calls.append(command)
        if command[:3] == ["pdftk", command[1], "dump_data_utf8"]:
            stdout = (
                "NumberOfPages: 2\n"
                "BookmarkBegin\n"
                "BookmarkTitle: A\n"
                "BookmarkLevel: 1\n"
                "BookmarkPageNumber: 1\n"
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        if command[0] == "qpdf" and command[1] == "--linearize":
            with open(command[-1], "w", encoding="utf-8") as handle:
                handle.write("out")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(pdf_toc_clean, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_toc_clean.subprocess, "run", _fake_run)

    result = pdf_toc_clean.run([str(input_pdf)])

    assert result == 0
    assert any(str(input_pdf.with_name("toc_toc-clean.pdf")) in cmd for cmd in calls)


@pytest.mark.parametrize(
    "spec, max_pages, expected",
    [
        ("3", 10, (3, 3)),
        ("3-", 10, (3, 10)),
        ("-3", 10, (1, 3)),
        ("3-7", 10, (3, 7)),
    ],
)
def test_parse_page_range_accepts_required_formats(spec, max_pages, expected):
    """
    @brief Validate accepted page-range grammar.
    @details Executes parser against required accepted forms and validates
      normalized start/end tuple.
    @param spec {str} Input page-range expression.
    @param max_pages {int} Document page upper bound.
    @param expected {tuple[int, int]} Expected normalized output.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-035
    """

    assert pdf_crop._parse_page_range(spec, max_pages, "--pages") == expected


@pytest.mark.parametrize("spec", ["", "1--2", "a", "0", "4-2", "1-20", "--3"])
def test_parse_page_range_rejects_invalid_formats(spec):
    """
    @brief Validate invalid page-range rejection.
    @details Executes parser against malformed or out-of-range expressions and
      asserts fail-fast termination via SystemExit.
    @param spec {str} Invalid page-range expression.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-035
    """

    with pytest.raises(SystemExit):
        pdf_crop._parse_page_range(spec, 10, "--pages")


def test_pdf_crop_run_supports_required_options(monkeypatch, tmp_path):
    """
    @brief Validate pdf-crop option handling and Ghostscript path.
    @details Mocks dependency checks, page metadata, bbox calculation, and
      conversion pipeline to assert support for --bbox, --margins,
      --analyze-pages, and --pages options.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-034
    """

    input_pdf = tmp_path / "crop.pdf"
    output_pdf = tmp_path / "crop-out.pdf"
    input_pdf.write_text("dummy")

    observed = {}

    def _fake_convert(input_f, output_f, first, last, cw, ch, cl, cb, total):
        """
        @brief Mock Ghostscript conversion helper.
        @details Captures normalized crop/export parameters and writes dummy
          output artifact for downstream metadata checks.
        @param input_f {str} Input PDF path.
        @param output_f {str} Output PDF path.
        @param first {int} First exported page index.
        @param last {int} Last exported page index.
        @param cw {float} Output width points.
        @param ch {float} Output height points.
        @param cl {float} Crop-left translation.
        @param cb {float} Crop-bottom translation.
        @param total {int} Total exported pages.
        @return {int} Zero success status.
        """

        observed["convert"] = {
            "input_f": input_f,
            "output_f": output_f,
            "first": first,
            "last": last,
            "cw": cw,
            "ch": ch,
            "cl": cl,
            "cb": cb,
            "total": total,
        }
        pathlib.Path(output_f).write_text("out")
        return 0

    def _fake_run(command, **kwargs):
        """
        @brief Mock subprocess.run for pdf-crop metadata probes.
        @details Returns deterministic pdfinfo box output for first-page query
          and success for all other subprocess invocations.
        @param command {list[str]} Command token vector.
        @param kwargs {dict[str, object]} Execution options.
        @return {subprocess.CompletedProcess[str]} Successful completion object.
        """

        del kwargs
        if command[:2] == ["pdfinfo", "-f"]:
            stdout = "Page    1 MediaBox: 0 0 200 300\nCropBox: 0 0 200 300\n"
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(pdf_crop, "require_commands", lambda *_cmds: None)
    monkeypatch.setattr(pdf_crop, "_get_page_count", lambda _pdf: 12)
    monkeypatch.setattr(
        pdf_crop, "_get_mediabox", lambda _pdf, page=1: (0, 0, 200, 300)
    )
    monkeypatch.setattr(
        pdf_crop, "_compute_auto_bbox", lambda *_args: (10, 20, 190, 280)
    )
    monkeypatch.setattr(pdf_crop, "_convert_pdf_with_progress", _fake_convert)
    monkeypatch.setattr(pdf_crop.subprocess, "run", _fake_run)

    result = pdf_crop.run(
        [
            "--in",
            str(input_pdf),
            "--out",
            str(output_pdf),
            "--bbox",
            "10 20 190 280",
            "--margins",
            "1 2 3 4",
            "--analyze-pages",
            "2-5",
            "--pages",
            "2-4",
        ]
    )

    assert result == 0
    assert observed["convert"]["first"] == 2
    assert observed["convert"]["last"] == 4
    assert observed["convert"]["total"] == 3


def test_pdf_tiler_090_checks_executable_before_exec(monkeypatch, tmp_path):
    """
    @brief Validate pre-exec command guard in pdf-tiler-090.
    @details Captures require_commands calls and confirms `plakativ` executable
      check occurs before process replacement.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {pathlib.Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-007, REQ-055, REQ-056
    """

    input_pdf = tmp_path / "doc.pdf"
    input_pdf.write_text("dummy")
    observed = []

    def _fake_require_commands(*cmds):
        """
        @brief Mock require_commands for guard verification.
        @details Records requested command tokens.
        @param cmds {tuple[str, ...]} Command tokens under validation.
        @return {None} Side effects only.
        """

        observed.append(cmds)

    def _fake_execvp(_executable, _args):
        """
        @brief Mock os.execvp boundary.
        @details Terminates execution flow to keep test deterministic.
        @throws {SystemExit} Forced termination for test boundary.
        @return {NoReturn} Function always raises.
        """

        raise SystemExit(0)

    monkeypatch.setattr(pdf_tiler_090, "require_commands", _fake_require_commands)
    monkeypatch.setattr(pdf_tiler_090.os, "execvp", _fake_execvp)

    with pytest.raises(SystemExit):
        pdf_tiler_090.run([str(input_pdf)])

    assert observed == [("plakativ",), ("plakativ",)]
