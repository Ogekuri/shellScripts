"""
@brief Validate `dng2hdr2jpg` command EV parsing and HDR merge contract.
@details Verifies argument validation, EV parsing/default behavior, three-
  bracket extraction multipliers, enfuse merge invocation, and temporary
  artifact cleanup for success/failure execution paths.
@satisfies TST-011, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059
@return {None} Pytest module scope.
"""

from pathlib import Path
import subprocess
import tempfile as std_tempfile
import tomllib

import pytest

import shell_scripts.commands.dng2hdr2jpg as dng2hdr2jpg

_ORIGINAL_TEMPORARY_DIRECTORY = std_tempfile.TemporaryDirectory


class _FakeScaledImage:
    """@brief Represent intermediate scaled image payload for fake IO pipeline.

    @details Implements clip/astype operations consumed by `dng2hdr2jpg` conversion
    path while preserving deterministic test-only behavior.
    @return {None} Stateful helper class.
    """

    def clip(self, _low, _high):
        """@brief Return self for deterministic chained conversion operations.

        @param _low {int|float} Minimum clipping bound.
        @param _high {int|float} Maximum clipping bound.
        @return {_FakeScaledImage} Self instance.
        """

        return self

    def astype(self, _dtype):
        """@brief Return deterministic uint8 payload marker.

        @param _dtype {str} Target dtype token.
        @return {str} Deterministic marker consumed by fake writer.
        """

        return "uint8-payload"


class _FakeImage16:
    """@brief Represent fake 16-bit image payload for conversion branch coverage.

    @details Exposes `dtype` metadata and division operation used by production
    conversion logic without requiring numpy dependency in tests.
    @return {None} Stateful helper class.
    """

    dtype = "uint16"

    def __truediv__(self, _value):
        """@brief Return scaled payload helper for conversion pipeline.

        @param _value {int|float} Divisor value.
        @return {_FakeScaledImage} Scaled payload helper.
        """

        return _FakeScaledImage()


class _FakeRawHandle:
    """@brief Minimal fake RAW handle for deterministic bracket extraction.

    @details Captures requested brightness multipliers from `postprocess` calls
    and returns marker payload objects for fake image writing.
    @return {None} Stateful helper class.
    """

    def __init__(self, observed):
        """@brief Initialize fake RAW handle state.

        @param observed {dict[str, object]} Shared observation map.
        @return {None} Constructor side effects only.
        """

        self._observed = observed

    def __enter__(self):
        """@brief Enter context-manager boundary.

        @return {_FakeRawHandle} Self instance.
        """

        return self

    def __exit__(self, exc_type, exc, tb):
        """@brief Exit context-manager boundary.

        @param exc_type {type|None} Raised exception type.
        @param exc {BaseException|None} Raised exception object.
        @param tb {object|None} Traceback object.
        @return {bool} `False` to propagate exceptions.
        """

        del exc_type, exc, tb
        return False

    def postprocess(self, bright, output_bps, no_auto_bright):
        """@brief Capture bracket extraction options and return payload marker.

        @param bright {float} Brightness multiplier.
        @param output_bps {int} Output bit depth.
        @param no_auto_bright {bool} Auto-bright disable flag.
        @return {str} Deterministic payload marker.
        """

        self._observed["brights"].append(bright)
        self._observed["output_bps"].append(output_bps)
        self._observed["no_auto_bright"].append(no_auto_bright)
        return f"rgb-{bright}"


class _TrackingTemporaryDirectory:
    """@brief Wrap TemporaryDirectory and expose created path for assertions.

    @details Delegates lifecycle management to standard `TemporaryDirectory`
    while recording generated path for post-run cleanup checks.
    @return {None} Stateful helper class.
    """

    def __init__(self, observed, *args, **kwargs):
        """@brief Initialize wrapped temporary directory.

        @param observed {dict[str, object]} Shared observation map.
        @param args {tuple[object, ...]} Positional args for wrapped constructor.
        @param kwargs {dict[str, object]} Keyword args for wrapped constructor.
        @return {None} Constructor side effects only.
        """

        self._observed = observed
        self._wrapped = _ORIGINAL_TEMPORARY_DIRECTORY(*args, **kwargs)

    def __enter__(self):
        """@brief Enter wrapped temporary-directory context.

        @return {str} Temporary directory path string.
        """

        directory = self._wrapped.__enter__()
        self._observed["tmp_dir"] = Path(directory)
        return directory

    def __exit__(self, exc_type, exc, tb):
        """@brief Exit wrapped temporary-directory context.

        @param exc_type {type|None} Raised exception type.
        @param exc {BaseException|None} Raised exception object.
        @param tb {object|None} Traceback object.
        @return {bool} Delegated wrapped-context return value.
        """

        return self._wrapped.__exit__(exc_type, exc, tb)


def test_dng2hdr2jpg_rejects_missing_required_positionals(tmp_path):
    """
    @brief Validate missing positional-argument guard.
    @details Provides incomplete argument vectors and asserts deterministic
      non-zero return code.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-055
    """

    del tmp_path
    assert dng2hdr2jpg.run([]) == 1
    assert dng2hdr2jpg.run(["input.dng"]) == 1


def test_dng2hdr2jpg_rejects_invalid_ev_value(tmp_path):
    """
    @brief Validate EV option parser rejects unsupported values.
    @details Uses unsupported EV value while providing required positional
      arguments and asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=3"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev", "bad"]) == 1


def test_dng2hdr2jpg_uses_default_ev_and_runs_hdr_pipeline(monkeypatch, tmp_path):
    """
    @brief Validate default EV behavior and complete HDR pipeline invocation.
    @details Mocks rawpy/imageio/subprocess boundaries and asserts multiplier
      sequence, enfuse command shape, JPG output creation, and temp cleanup.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056, REQ-057, REQ-058, REQ-059
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "no_auto_bright": [],
        "writes": [],
        "enfuse_cmd": None,
        "tmp_dir": None,
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for command tests.

        @details Exposes `imread` factory and a runtime error class expected by
        `_collect_processing_errors`.
        @return {None} Helper class.
        """

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager for the provided path.

            @param _path {str} Input DNG path.
            @return {_FakeRawHandle} Fake RAW handle.
            """

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module surface for command tests.

        @details Creates deterministic files for bracket/merged/output write
        assertions and returns fake image payload for JPG encode step.
        @return {None} Helper class.
        """

        @staticmethod
        def imwrite(path, _data):
            """@brief Write deterministic fake payload to requested path.

            @param path {str} Destination file path.
            @param _data {object} Image payload marker.
            @return {None} Side effects only.
            """

            observed["writes"].append(Path(path).name)
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for conversion branch.

            @param path {str} Source file path.
            @return {_FakeImage16} Fake image payload.
            """

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture enfuse invocation and materialize merged TIFF output.

        @param command {list[str]} Subprocess argv vector.
        @param check {bool} Subprocess check flag.
        @return {subprocess.CompletedProcess[str]} Deterministic success object.
        """

        assert check is True
        observed["enfuse_cmd"] = command
        output_flag = next(token for token in command if token.startswith("--output="))
        merged_path = Path(output_flag.split("=", 1)[1])
        merged_path.write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(dng2hdr2jpg, "_load_image_dependencies", lambda: (_FakeRawPyModule, _FakeImageIoModule))
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(
        dng2hdr2jpg.tempfile,
        "TemporaryDirectory",
        lambda *args, **kwargs: _TrackingTemporaryDirectory(observed, *args, **kwargs),
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg)])

    assert result == 0
    assert observed["brights"] == pytest.approx([0.25, 1.0, 4.0])
    assert observed["output_bps"] == [16, 16, 16]
    assert observed["no_auto_bright"] == [True, True, True]
    assert observed["enfuse_cmd"][0] == "enfuse"
    assert len(observed["enfuse_cmd"]) == 6
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_returns_error_and_cleans_temp_on_enfuse_failure(monkeypatch, tmp_path):
    """
    @brief Validate merge failure path returns non-zero and cleans artifacts.
    @details Mocks subprocess merge call to raise `CalledProcessError`, then
      asserts error return code and temporary directory deletion.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-058, REQ-059
    """

    observed = {"tmp_dir": None}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for failure-path test.

        @details Exposes raw handle factory and error class surface used by
        processing exception collector.
        @return {None} Helper class.
        """

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle.

            @param _path {str} Input DNG path.
            @return {_FakeRawHandle} Fake RAW handle.
            """

            return _FakeRawHandle({"brights": [], "output_bps": [], "no_auto_bright": []})

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for failure-path test.

        @details Writes deterministic placeholders and is not expected to read
        merged payload because merge fails first.
        @return {None} Helper class.
        """

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder file.

            @param path {str} Destination path.
            @param _data {object} Payload marker.
            @return {None} Side effects only.
            """

            Path(path).write_text("payload", encoding="utf-8")

    def _fake_subprocess_run(command, check):
        """@brief Raise deterministic merge failure from fake subprocess.

        @param command {list[str]} Subprocess argv vector.
        @param check {bool} Subprocess check flag.
        @return {subprocess.CompletedProcess[str]} Unused because exception path.
        @exception subprocess.CalledProcessError Always raised for failure path.
        """

        assert check is True
        raise subprocess.CalledProcessError(2, command)

    monkeypatch.setattr(dng2hdr2jpg, "_load_image_dependencies", lambda: (_FakeRawPyModule, _FakeImageIoModule))
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(
        dng2hdr2jpg.tempfile,
        "TemporaryDirectory",
        lambda *args, **kwargs: _TrackingTemporaryDirectory(observed, *args, **kwargs),
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=1.5"])

    assert result == 1
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_fails_when_enfuse_dependency_is_missing(monkeypatch, tmp_path):
    """
    @brief Validate missing `enfuse` dependency path.
    @details Forces missing executable lookup and asserts deterministic non-zero
      return code before image processing starts.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda _cmd: None)

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg)]) == 1


def test_dng2hdr2jpg_returns_error_on_windows_runtime(monkeypatch, tmp_path):
    """
    @brief Validate Linux-only guard for Windows runtime.
    @details Forces runtime OS label to `windows` and asserts command rejection
      with deterministic non-zero return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-055, REQ-059
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "windows")

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg)]) == 1


def test_dng2hdr2jpg_returns_error_on_macos_runtime(monkeypatch, tmp_path):
    """
    @brief Validate Linux-only guard for macOS runtime.
    @details Forces runtime OS label to `darwin` and asserts command rejection
      with deterministic non-zero return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-055, REQ-059
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "darwin")

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg)]) == 1


def test_dng2hdr2jpg_runtime_dependencies_are_declared_in_pyproject():
    """
    @brief Validate runtime dependency declaration for DNG processing modules.
    @details Parses `pyproject.toml` and asserts that `rawpy` and `imageio`
      are declared in `project.dependencies` so uv tool installs provide command
      runtime requirements without manual post-install steps.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059
    """

    project_root = Path(__file__).resolve().parents[1]
    pyproject_path = project_root / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = pyproject_data["project"].get("dependencies", [])

    assert any(dep.startswith("rawpy") for dep in dependencies)
    assert any(dep.startswith("imageio") for dep in dependencies)
