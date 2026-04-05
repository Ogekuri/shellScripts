"""
@brief Validate FFmpeg video conversion command wrappers.
@details Verifies `video2h264` and `video2h265` command argument validation,
  output path generation semantics, exact FFmpeg argv construction, and
  subprocess return-code propagation.
@satisfies TST-011, REQ-057, REQ-058, REQ-064
@return {None} Pytest module scope.
"""

import types

import shell_scripts.commands.video2h264 as video2h264
import shell_scripts.commands.video2h265 as video2h265


def test_video2h264_run_execs_ffmpeg_with_required_options(monkeypatch, tmp_path):
    """@brief Validate H.264 FFmpeg argv construction.

    @details Creates one temporary input file, intercepts executable checks and
    subprocess boundary, and asserts required fixed encoder flags plus output
    suffix and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Temporary filesystem root.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-055, REQ-056, REQ-064
    """

    input_file = tmp_path / "input.mov"
    input_file.write_bytes(b"x")
    observed = {}

    monkeypatch.setattr(
        video2h264,
        "require_commands",
        lambda command: observed.__setitem__("checked", command),
    )

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=30)

    monkeypatch.setattr(video2h264.subprocess, "run", _fake_run)

    result = video2h264.run([str(input_file)])

    expected_output = str(tmp_path / "input.mov.mp4")
    assert result == 30
    assert observed["checked"] == "ffmpeg"
    assert observed["kwargs"] == {}
    assert observed["command"] == [
        "ffmpeg",
        "-i",
        str(input_file),
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        expected_output,
    ]


def test_video2h265_run_execs_ffmpeg_with_required_options(monkeypatch, tmp_path):
    """@brief Validate H.265 FFmpeg argv construction.

    @details Creates one temporary input file, intercepts executable checks and
    subprocess boundary, and asserts required fixed encoder flags plus output
    suffix and propagated return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Temporary filesystem root.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-058, REQ-055, REQ-056, REQ-064
    """

    input_file = tmp_path / "input.mov"
    input_file.write_bytes(b"x")
    observed = {}

    monkeypatch.setattr(
        video2h265,
        "require_commands",
        lambda command: observed.__setitem__("checked", command),
    )

    def _fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return types.SimpleNamespace(returncode=31)

    monkeypatch.setattr(video2h265.subprocess, "run", _fake_run)

    result = video2h265.run([str(input_file)])

    expected_output = str(tmp_path / "input.mov.mp4")
    assert result == 31
    assert observed["checked"] == "ffmpeg"
    assert observed["kwargs"] == {}
    assert observed["command"] == [
        "ffmpeg",
        "-i",
        str(input_file),
        "-c:v",
        "libx265",
        "-crf",
        "23",
        "-tag:v",
        "hvc1",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        expected_output,
    ]


def test_video_command_requires_input_file(capsys):
    """@brief Validate missing-input error path.

    @details Calls command runner with empty args and validates deterministic
    non-zero return plus explicit input-required error emission.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-058
    """

    result_h264 = video2h264.run([])
    err_h264 = capsys.readouterr().err
    assert result_h264 == 1
    assert "Input video file required." in err_h264

    result_h265 = video2h265.run([])
    err_h265 = capsys.readouterr().err
    assert result_h265 == 1
    assert "Input video file required." in err_h265


def test_video_command_requires_existing_file(tmp_path, capsys):
    """@brief Validate nonexistent-file rejection path.

    @details Calls both commands with absent path and verifies deterministic
    non-zero return plus explicit file-not-found error output.
    @param tmp_path {Path} Temporary filesystem root.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-058
    """

    missing = tmp_path / "missing.mov"

    result_h264 = video2h264.run([str(missing)])
    err_h264 = capsys.readouterr().err
    assert result_h264 == 1
    assert f"File not found: {missing}" in err_h264

    result_h265 = video2h265.run([str(missing)])
    err_h265 = capsys.readouterr().err
    assert result_h265 == 1
    assert f"File not found: {missing}" in err_h265


def test_main_help_lists_new_video_commands(monkeypatch, capsys):
    """@brief Validate global help contains new command names.

    @details Forces global help rendering path and asserts registry exposure of
    `video2h264` and `video2h265` entries.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture helper.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-058
    """

    import shell_scripts.core as core

    monkeypatch.setattr(core, "check_for_updates", lambda _version: None)
    monkeypatch.setattr(core.sys, "argv", ["shellscripts"])

    result = core.main()
    output = capsys.readouterr().out

    assert result == 0
    assert "video2h264" in output
    assert "video2h265" in output
