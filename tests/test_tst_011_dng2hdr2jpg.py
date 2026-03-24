"""
@brief Validate `dng2hdr2jpg` command EV parsing and HDR merge contract.
@details Verifies argument validation, EV parsing/default behavior, three-
  bracket extraction multipliers, dual-backend HDR merge behavior, shared
  postprocessing options, and temporary artifact cleanup semantics.
@satisfies TST-011, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069
@return {None} Pytest module scope.
"""

from pathlib import Path
from importlib import import_module
import sys
import subprocess
import tempfile as std_tempfile
import tomllib

import pytest

PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

dng2hdr2jpg = import_module("shell_scripts.commands.dng2hdr2jpg")

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

    def postprocess(self, bright, output_bps, use_camera_wb, no_auto_bright, gamma):
        """@brief Capture bracket extraction options and return payload marker.

        @param bright {float} Brightness multiplier.
        @param output_bps {int} Output bit depth.
        @param use_camera_wb {bool} Camera white-balance enable flag.
        @param no_auto_bright {bool} Auto-bright disable flag.
        @param gamma {tuple[float, float]} Raw gamma pair.
        @return {str} Deterministic payload marker.
        """

        self._observed["brights"].append(bright)
        self._observed["output_bps"].append(output_bps)
        self._observed["use_camera_wb"].append(use_camera_wb)
        self._observed["no_auto_bright"].append(no_auto_bright)
        self._observed["gamma"].append(gamma)
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


def _build_fake_pillow_modules(observed):
    """@brief Build fake Pillow modules for deterministic postprocess testing.

    @details Creates `Image.fromarray` and `ImageEnhance` replacements that
      preserve production call-shape while recording transformation effects.
    @param observed {dict[str, object]} Shared mutable assertion map.
    @return {tuple[type, type]} Fake `(Image, ImageEnhance)` module pair.
    """

    class _FakePilImage:
        """@brief Fake Pillow image object with conversion/save surface."""

        def __init__(self, payload):
            """@brief Store payload-derived mode for conversion assertions."""

            self.mode = getattr(payload, "mode", "RGB")

        def getbands(self):
            """@brief Return channels matching current mode."""

            if self.mode == "RGBA":
                return ("R", "G", "B", "A")
            return ("R", "G", "B")

        def point(self, _lut):
            """@brief Record LUT application and return self."""

            observed.setdefault("postprocess_ops", []).append("gamma")
            return self

        def convert(self, target_mode):
            """@brief Switch mode and record conversion."""

            observed.setdefault("pil_conversions", []).append((self.mode, target_mode))
            self.mode = target_mode
            return self

        def save(self, path, format, quality, optimize):
            """@brief Persist deterministic JPEG artifact and record encode args."""

            observed["jpg_save"] = {
                "format": format,
                "quality": quality,
                "optimize": optimize,
                "mode": self.mode,
            }
            Path(path).write_text("jpg", encoding="utf-8")

    class _FakeEnhancer:
        """@brief Fake Pillow enhancer object with factor capture."""

        def __init__(self, image, op_name):
            """@brief Initialize enhancer with operation name."""

            self._image = image
            self._op_name = op_name

        def enhance(self, value):
            """@brief Record enhancement factor and return original image."""

            observed.setdefault("postprocess_ops", []).append((self._op_name, value))
            return self._image

    class _FakePilImageModule:
        """@brief Fake Pillow Image module exposing `fromarray`."""

        @staticmethod
        def fromarray(payload):
            """@brief Build fake image from array-like payload."""

            return _FakePilImage(payload)

    class _FakePilEnhanceModule:
        """@brief Fake Pillow ImageEnhance module."""

        @staticmethod
        def Brightness(image):
            """@brief Return brightness enhancer."""

            return _FakeEnhancer(image, "brightness")

        @staticmethod
        def Contrast(image):
            """@brief Return contrast enhancer."""

            return _FakeEnhancer(image, "contrast")

        @staticmethod
        def Color(image):
            """@brief Return saturation enhancer."""

            return _FakeEnhancer(image, "saturation")

    return _FakePilImageModule, _FakePilEnhanceModule


def _build_fake_dependencies(raw_module, imageio_module, observed):
    """@brief Build runtime dependency tuple for `_load_image_dependencies`.

    @details Extends fake rawpy/imageio modules with fake Pillow modules so test
      doubles match production dependency-loading contract.
    @param raw_module {type} Fake rawpy module.
    @param imageio_module {type} Fake imageio module.
    @param observed {dict[str, object]} Shared mutable assertion map.
    @return {tuple[type, type, type, type]} Fake dependency tuple.
    """

    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)
    return raw_module, imageio_module, pil_image_module, pil_enhance_module


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
    @satisfies TST-011, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
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

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
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
    assert observed["use_camera_wb"] == [True, True, True]
    assert observed["no_auto_bright"] == [True, True, True]
    assert observed["gamma"] == [(2.222, 4.5), (2.222, 4.5), (2.222, 4.5)]
    assert observed["enfuse_cmd"][0] == "enfuse"
    assert len(observed["enfuse_cmd"]) == 6
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_runs_luminance_backend_with_default_operator(monkeypatch, tmp_path):
    """
    @brief Validate luminance-hdr-cli backend execution with default parameters.
    @details Enables luminance mode and verifies command argv shape uses
      `luminance-hdr-cli -e <ev-list> --hdrModel debevec --hdrWeight triangular`
      `--hdrResponseCurve srgb --tmo mantiuk08 --tmoM08ColorSaturation 1`
      `--tmoM08ConstrastEnh 0.25 -o <merged_hdr.tif>`
      plus three bracket TIFF inputs.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-060, REQ-061, REQ-062
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "luminance_cmd": None,
        "tmp_dir": None,
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for luminance backend test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager for the provided path."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for bracket TIFF extraction only."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic intermediate files."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for shared JPG encode stage."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture luminance-hdr-cli invocation and materialize output JPG."""

        assert check is True
        observed["luminance_cmd"] = command
        output_index = command.index("-o") + 1
        Path(command[output_index]).write_text("jpg", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(
        dng2hdr2jpg.tempfile,
        "TemporaryDirectory",
        lambda *args, **kwargs: _TrackingTemporaryDirectory(observed, *args, **kwargs),
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance", "--ev=1"])

    assert result == 0
    assert observed["brights"] == pytest.approx([0.5, 1.0, 2.0])
    assert observed["output_bps"] == [16, 16, 16]
    assert observed["use_camera_wb"] == [True, True, True]
    assert observed["no_auto_bright"] == [True, True, True]
    assert observed["gamma"] == [(2.222, 4.5), (2.222, 4.5), (2.222, 4.5)]
    assert observed["luminance_cmd"][0] == "luminance-hdr-cli"
    assert observed["luminance_cmd"][1:16] == [
        "-e",
        "-1,0,1",
        "--hdrModel",
        "debevec",
        "--hdrWeight",
        "triangular",
        "--hdrResponseCurve",
        "srgb",
        "--tmo",
        "mantiuk08",
        "--tmoM08ColorSaturation",
        "1",
        "--tmoM08ConstrastEnh",
        "0.25",
        "-o",
    ]
    assert Path(observed["luminance_cmd"][16]).name == "merged_hdr.tif"
    assert [Path(value).name for value in observed["luminance_cmd"][17:]] == [
        "ev_minus.tif",
        "ev_zero.tif",
        "ev_plus.tif",
    ]
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_runs_luminance_backend_with_custom_params(monkeypatch, tmp_path):
    """
    @brief Validate simplified luminance options map to command argv.
    @details Uses custom luminance backend values and asserts deterministic
      argument order with EV sequence and bracket path order.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060, REQ-061, REQ-062, REQ-067, REQ-068
    """

    observed = {"command": []}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for map alias test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle."""

            return _FakeRawHandle(
                {"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []}
            )

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for bracket writes."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder files."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for shared JPG encode stage."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture command and materialize luminance output."""

        assert check is True
        observed["command"] = command
        output_index = command.index("-o") + 1
        Path(command[output_index]).write_text("jpg", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-luminance",
            "--luminance-hdr-model=robertson",
            "--luminance-hdr-weight=gaussian",
            "--luminance-hdr-response-curve=from_file",
            "--luminance-tmo=fattal",
            "--luminance-m08-color-saturation=1.2",
            "--luminance-m08-contrast-enh=0.4",
        ]
    )

    assert result == 0
    command = observed["command"]
    assert command
    assert command[0] == "luminance-hdr-cli"
    assert command[1:16] == [
        "-e",
        "-2,0,2",
        "--hdrModel",
        "robertson",
        "--hdrWeight",
        "gaussian",
        "--hdrResponseCurve",
        "from_file",
        "--tmo",
        "fattal",
        "--tmoM08ColorSaturation",
        "1.2",
        "--tmoM08ConstrastEnh",
        "0.4",
        "-o",
    ]
    assert Path(command[16]).name == "merged_hdr.tif"
    assert [Path(value).name for value in command[17:]] == ["ev_minus.tif", "ev_zero.tif", "ev_plus.tif"]


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

            return _FakeRawHandle(
                {"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []}
            )

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

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
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


def test_dng2hdr2jpg_rejects_invalid_gamma_value(tmp_path):
    """
    @brief Validate gamma option parser rejects malformed values.
    @details Provides malformed, non-numeric, and non-positive gamma values and
      asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-064
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--gamma=1"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--gamma=a,b"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--gamma=0,1"]) == 1


def test_dng2hdr2jpg_rejects_invalid_postprocess_values(tmp_path):
    """
    @brief Validate postprocess and JPEG-compression parser rejections.
    @details Provides malformed or out-of-range values for postprocess options
      and asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--post-gamma=0"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--brightness=foo"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--contrast=-1"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--saturation=0"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--jpg-compression=200"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--jpg-compression=bad"]) == 1


def test_dng2hdr2jpg_applies_custom_gamma_value(monkeypatch, tmp_path):
    """
    @brief Validate custom gamma option is propagated to RAW postprocess calls.
    @details Runs default backend with `--gamma=1,1` and verifies all bracket
      extraction calls receive the selected gamma pair.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-064
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "writes": [],
        "enfuse_cmd": None,
        "tmp_dir": None,
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for custom gamma test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager for custom gamma test."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module surface for custom gamma test."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic fake payload file."""

            observed["writes"].append(Path(path).name)
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for encode path."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture enfuse invocation and materialize merged output."""

        assert check is True
        observed["enfuse_cmd"] = command
        output_flag = next(token for token in command if token.startswith("--output="))
        merged_path = Path(output_flag.split("=", 1)[1])
        merged_path.write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
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

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--gamma=1,1"])

    assert result == 0
    assert observed["gamma"] == [(1.0, 1.0), (1.0, 1.0), (1.0, 1.0)]


def test_dng2hdr2jpg_reorders_luminance_brackets(monkeypatch, tmp_path):
    """
    @brief Validate luminance backend enforces deterministic bracket ordering.
    @details Overrides bracket writer to return shuffled exposure paths and
      asserts luminance command reorders them as `ev_minus,ev_zero,ev_plus`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-062
    """

    observed = {"command": []}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for bracket ordering test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle for luminance ordering test."""

            return _FakeRawHandle({"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []})

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for bracket ordering test."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder file."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake merged payload for shared postprocess stage."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture luminance command and materialize merged TIFF output."""

        assert check is True
        observed["command"] = command
        output_index = command.index("-o") + 1
        Path(command[output_index]).write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def _fake_write_brackets(raw_handle, imageio_module, multipliers, gamma_value, temp_dir):
        """@brief Return shuffled bracket list for reorder validation."""

        del raw_handle, imageio_module, multipliers, gamma_value
        paths = [
            temp_dir / "ev_zero.tif",
            temp_dir / "ev_plus.tif",
            temp_dir / "ev_minus.tif",
        ]
        for path in paths:
            path.write_text("payload", encoding="utf-8")
        return paths

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_write_bracket_images", _fake_write_brackets)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance"])

    assert result == 0
    command = observed["command"]
    assert command
    assert [Path(value).name for value in command[-3:]] == ["ev_minus.tif", "ev_zero.tif", "ev_plus.tif"]


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


def test_dng2hdr2jpg_fails_when_luminance_dependency_is_missing(monkeypatch, tmp_path):
    """
    @brief Validate missing `luminance-hdr-cli` dependency in luminance mode.
    @details Enables luminance backend with missing executable lookup and
      asserts deterministic non-zero return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060, REQ-059
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: None if cmd == "luminance-hdr-cli" else "/usr/bin/enfuse",
    )

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance"]) == 1


def test_dng2hdr2jpg_rejects_luminance_options_without_enable(tmp_path):
    """
    @brief Validate luminance options require enable flag.
    @details Uses luminance option selectors without backend enable flag and
      asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-061
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--luminance-tmo=fattal"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--luminance-hdr-model=robertson"]) == 1


def test_dng2hdr2jpg_rejects_malformed_luminance_options(monkeypatch, tmp_path):
    """
    @brief Validate malformed luminance options are rejected.
    @details Provides empty and non-positive luminance values and asserts
      deterministic parse failure.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-061, REQ-067
    """

    del monkeypatch
    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance", "--luminance-tmo="]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance", "--luminance-hdr-model", ""]) == 1
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-luminance", "--luminance-m08-color-saturation=0"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-luminance", "--luminance-m08-contrast-enh=-1"]
        )
        == 1
    )


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
    @details Parses `pyproject.toml` and asserts that `rawpy`, `imageio`, and
      `pillow`
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
    assert any(dep.startswith("pillow") for dep in dependencies)


def test_dng2hdr2jpg_handles_rgba_merged_image_for_jpeg_output(tmp_path):
    """
    @brief Validate JPG encode path strips alpha channel from merged HDR payload.
    @details Simulates merged HDR decode that yields RGBA payload; encoder must
      convert payload to RGB-compatible data before final JPEG write.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-058, REQ-059
    """

    observed = {"jpg_save": None}

    class _FakeRgbaPayload:
        """@brief Minimal RGBA payload object consumed by fake Pillow."""

        mode = "RGBA"

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for RGBA encode reproducer."""

        @staticmethod
        def imread(path):
            """@brief Return fake RGBA payload for merged HDR TIFF input."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeRgbaPayload()

    merged_tiff = tmp_path / "merged_hdr.tif"
    merged_tiff.write_text("merged", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)

    dng2hdr2jpg._encode_jpg(
        imageio_module=_FakeImageIoModule,
        pil_image_module=pil_image_module,
        pil_enhance_module=pil_enhance_module,
        merged_tiff=merged_tiff,
        output_jpg=output_jpg,
        postprocess_options=dng2hdr2jpg.PostprocessOptions(
            post_gamma=1.0,
            brightness=1.0,
            contrast=1.0,
            saturation=1.0,
            jpg_compression=10,
        ),
    )

    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["mode"] == "RGB"
    assert output_jpg.exists()


def test_dng2hdr2jpg_help_includes_luminance_options(capsys):
    """
    @brief Validate command help documents luminance backend options.
    @details Calls help renderer and asserts presence of luminance enable flag,
      simplified luminance selectors, and postprocess selectors.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-063, REQ-067
    """

    dng2hdr2jpg.print_help("0.0.0")
    captured = capsys.readouterr()
    output = captured.out

    assert "--enable-luminance" in output
    assert "--gamma=<a,b>" in output
    assert "--post-gamma=<value>" in output
    assert "--brightness=<value>" in output
    assert "--contrast=<value>" in output
    assert "--saturation=<value>" in output
    assert "--jpg-compression=<0..100>" in output
    assert "--luminance-hdr-model=<name>" in output
    assert "--luminance-hdr-weight=<name>" in output
    assert "--luminance-hdr-response-curve=<name>" in output
    assert "--luminance-tmo=<name>" in output
    assert "--luminance-m08-color-saturation=<value>" in output
    assert "--luminance-m08-contrast-enh=<value>" in output


def test_dng2hdr2jpg_applies_postprocess_controls_and_quality_mapping(tmp_path):
    """
    @brief Validate shared postprocess controls and JPEG quality mapping.
    @details Executes encode path with non-default gamma/brightness/contrast/
      saturation factors and verifies fake Pillow operations and quality value.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066
    """

    observed = {}

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for postprocess assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for conversion and postprocess."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    merged_tiff = tmp_path / "merged_hdr.tif"
    merged_tiff.write_text("merged", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)

    dng2hdr2jpg._encode_jpg(
        imageio_module=_FakeImageIoModule,
        pil_image_module=pil_image_module,
        pil_enhance_module=pil_enhance_module,
        merged_tiff=merged_tiff,
        output_jpg=output_jpg,
        postprocess_options=dng2hdr2jpg.PostprocessOptions(
            post_gamma=2.2,
            brightness=1.1,
            contrast=0.9,
            saturation=1.3,
            jpg_compression=80,
        ),
    )

    assert "gamma" in observed["postprocess_ops"]
    assert ("brightness", 1.1) in observed["postprocess_ops"]
    assert ("contrast", 0.9) in observed["postprocess_ops"]
    assert ("saturation", 1.3) in observed["postprocess_ops"]
    assert observed["jpg_save"]["quality"] == 20
    assert output_jpg.exists()
