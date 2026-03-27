"""
@brief Validate `video2h264`/`video2h265` command verification contract.

@details Verifies requirement-driven test coverage for video transcoding commands
using deterministic monkeypatched dependency and subprocess boundaries. Asserts
argument-validation failures for missing positional input, exact ffmpeg argv
composition per codec profile, and `<input>.mp4` output naming semantics.
@satisfies TST-012, REQ-095, REQ-096, REQ-097, REQ-098
@return {None} Pytest module scope.
"""

from pathlib import Path
import types

import shell_scripts.commands.video2h264 as video2h264
import shell_scripts.commands.video2h265 as video2h265


def test_video2h264_rejects_missing_required_input_argument() -> None:
    """@brief Validate `video2h264` missing-input guard.

    @details Executes command with no positional argument and with option-like
    first token, asserting deterministic non-zero failure status.
    @return {None} Assertions only.
    @satisfies TST-012, REQ-095
    """

    assert video2h264.run([]) == 1
    assert video2h264.run(["--invalid"]) == 1


def test_video2h264_builds_exact_ffmpeg_argv_and_output_suffix(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """@brief Validate `video2h264` ffmpeg argv contract.

    @details Monkeypatches dependency checks and subprocess execution, then
    asserts exact ffmpeg argument vector and `<input>.mp4` output naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-012, REQ-096
    """

    input_path = tmp_path / "clip.mov"
    input_path.write_text("dummy")
    require_calls: list[tuple[str, ...]] = []
    observed_command: list[str] | None = None

    def _fake_require_commands(*cmds: str) -> None:
        """@brief Capture required executable names.

        @details Records command-name tuple passed to dependency guard.
        @param cmds {tuple[str, ...]} Required executable names.
        @return {None} Side effects only.
        """

        require_calls.append(cmds)

    def _fake_run(command: list[str]):
        """@brief Capture ffmpeg subprocess argv.

        @details Records command vector and returns deterministic status code.
        @param command {list[str]} Executed subprocess argv.
        @return {types.SimpleNamespace} Object exposing `returncode`.
        """

        nonlocal observed_command
        observed_command = command
        return types.SimpleNamespace(returncode=7)

    monkeypatch.setattr(video2h264, "require_commands", _fake_require_commands)
    monkeypatch.setattr(video2h264.subprocess, "run", _fake_run)

    result = video2h264.run([str(input_path)])

    expected_output = Path(f"{input_path}.mp4")
    assert result == 7
    assert require_calls == [("ffmpeg",)]
    assert observed_command == [
        "ffmpeg",
        "-i",
        str(input_path),
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
        str(expected_output),
    ]


def test_video2h265_rejects_missing_required_input_argument() -> None:
    """@brief Validate `video2h265` missing-input guard.

    @details Executes command with no positional argument and with option-like
    first token, asserting deterministic non-zero failure status.
    @return {None} Assertions only.
    @satisfies TST-012, REQ-097
    """

    assert video2h265.run([]) == 1
    assert video2h265.run(["--invalid"]) == 1


def test_video2h265_builds_exact_ffmpeg_argv_and_output_suffix(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """@brief Validate `video2h265` ffmpeg argv contract.

    @details Monkeypatches dependency checks and subprocess execution, then
    asserts exact ffmpeg argument vector and `<input>.mp4` output naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-012, REQ-098
    """

    input_path = tmp_path / "clip.mkv"
    input_path.write_text("dummy")
    require_calls: list[tuple[str, ...]] = []
    observed_command: list[str] | None = None

    def _fake_require_commands(*cmds: str) -> None:
        """@brief Capture required executable names.

        @details Records command-name tuple passed to dependency guard.
        @param cmds {tuple[str, ...]} Required executable names.
        @return {None} Side effects only.
        """

        require_calls.append(cmds)

    def _fake_run(command: list[str]):
        """@brief Capture ffmpeg subprocess argv.

        @details Records command vector and returns deterministic status code.
        @param command {list[str]} Executed subprocess argv.
        @return {types.SimpleNamespace} Object exposing `returncode`.
        """

        nonlocal observed_command
        observed_command = command
        return types.SimpleNamespace(returncode=3)

    monkeypatch.setattr(video2h265, "require_commands", _fake_require_commands)
    monkeypatch.setattr(video2h265.subprocess, "run", _fake_run)

    result = video2h265.run([str(input_path)])

    expected_output = Path(f"{input_path}.mp4")
    assert result == 3
    assert require_calls == [("ffmpeg",)]
    assert observed_command == [
        "ffmpeg",
        "-i",
        str(input_path),
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
        str(expected_output),
    ]
