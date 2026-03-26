"""
@brief Validate `dng2hdr2jpg` command EV parsing and HDR merge contract.
@details Verifies argument validation, EV parsing/default behavior, three-
  bracket extraction multipliers, dual-backend HDR merge behavior, shared
  postprocessing options, and temporary artifact cleanup semantics.
@satisfies TST-011, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075
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

for module_name in ("shell_scripts.commands.dng2hdr2jpg", "shell_scripts.commands", "shell_scripts"):
    sys.modules.pop(module_name, None)
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

        def save(
            self,
            path,
            format,
            quality=None,
            optimize=None,
            compress_level=None,
            compression=None,
            exif=None,
        ):
            """@brief Persist deterministic JPEG artifact and record encode args."""

            del exif
            observed["jpg_save"] = {
                "format": format,
                "quality": quality,
                "optimize": optimize,
                "compress_level": compress_level,
                "compression": compression,
                "mode": self.mode,
            }
            if format == "PNG":
                observed.setdefault("png_save", []).append(Path(path).name)
                Path(path).write_text("png", encoding="utf-8")
                return
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
    @satisfies TST-011, REQ-056, REQ-060
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--ev=3"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--ev", "bad"]) == 1


def test_dng2hdr2jpg_rejects_missing_or_duplicated_backend_selector(tmp_path):
    """
    @brief Validate backend selector exclusivity and requiredness.
    @details Verifies parser rejects calls without selector and calls with both
      selectors together.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg)]) == 1
    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--enable-luminance"])
        == 1
    )


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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse"])

    assert result == 0
    assert observed["brights"] == pytest.approx([0.25, 1.0, 4.0])
    assert observed["output_bps"] == [16, 16, 16]
    assert observed["use_camera_wb"] == [True, True, True]
    assert observed["no_auto_bright"] == [True, True, True]
    assert observed["gamma"] == [(2.222, 4.5), (2.222, 4.5), (2.222, 4.5)]
    assert observed["enfuse_cmd"][0] == "enfuse"
    assert len(observed["enfuse_cmd"]) == 6
    assert "postprocess_ops" not in observed
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_runs_luminance_backend_with_default_operator(monkeypatch, tmp_path):
    """
    @brief Validate luminance-hdr-cli backend execution with default parameters.
    @details Enables luminance mode and verifies command argv shape uses
      `luminance-hdr-cli -e <ev-list> --hdrModel debevec --hdrWeight flat`
      `--hdrResponseCurve srgb --tmo reinhard02 --ldrTiff 16b -o <merged_hdr.tif>`
      plus three ordered bracket TIFF inputs.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-060, REQ-061, REQ-062, REQ-068, REQ-069
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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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
    assert observed["luminance_cmd"][1:14] == [
        "-e",
        "-1,0,1",
        "--hdrModel",
        "debevec",
        "--hdrWeight",
        "flat",
        "--hdrResponseCurve",
        "srgb",
        "--tmo",
        "reinhard02",
        "--ldrTiff",
        "16b",
        "-o",
    ]
    assert Path(observed["luminance_cmd"][14]).name == "merged_hdr.tif"
    assert [Path(value).name for value in observed["luminance_cmd"][15:]] == [
        "ev_minus.tif",
        "ev_zero.tif",
        "ev_plus.tif",
    ]
    assert ("brightness", 1.25) in observed["postprocess_ops"]
    assert ("contrast", 0.85) in observed["postprocess_ops"]
    assert ("saturation", 0.55) in observed["postprocess_ops"]
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_runs_luminance_backend_with_custom_params(monkeypatch, tmp_path):
    """
    @brief Validate luminance `--tmo*` passthrough options map to command argv.
    @details Uses custom luminance backend values plus explicit `--tmo*`
      passthrough arguments and asserts deterministic argument order with EV
      sequence and bracket path order.
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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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
            "--luminance-tmo=reinhard05",
            "--tmoR05Brightness",
            "0",
            "--tmoR05Chroma=1.1",
            "--tmoR05Lightness",
            "1.2",
        ]
    )

    assert result == 0
    command = observed["command"]
    assert command
    assert command[0] == "luminance-hdr-cli"
    assert command[1:20] == [
        "-e",
        "-2,0,2",
        "--hdrModel",
        "robertson",
        "--hdrWeight",
        "gaussian",
        "--hdrResponseCurve",
        "from_file",
        "--tmo",
        "reinhard05",
        "--ldrTiff",
        "16b",
        "--tmoR05Brightness",
        "0",
        "--tmoR05Chroma",
        "1.1",
        "--tmoR05Lightness",
        "1.2",
        "-o",
    ]
    assert Path(command[20]).name == "merged_hdr.tif"
    assert [Path(value).name for value in command[21:]] == ["ev_minus.tif", "ev_zero.tif", "ev_plus.tif"]


def test_dng2hdr2jpg_luminance_non_reinhard_defaults_remain_neutral(monkeypatch, tmp_path):
    """
    @brief Validate neutral postprocess defaults for non-`reinhard02` luminance TMO.
    @details Selects luminance backend with `--luminance-tmo=drago` and asserts
      no implicit postprocess enhancements are applied.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060, REQ-061, REQ-071
    """

    observed = {"command": []}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for neutral luminance defaults test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle."""

            return _FakeRawHandle(
                {"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []}
            )

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for neutral luminance defaults test."""

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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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
        [str(input_dng), str(output_jpg), "--enable-luminance", "--luminance-tmo=drago"]
    )

    assert result == 0
    assert "--tmo" in observed["command"]
    tmo_index = observed["command"].index("--tmo")
    assert observed["command"][tmo_index + 1] == "drago"
    assert "postprocess_ops" not in observed


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

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--ev=1.5"])

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
    @satisfies TST-011, REQ-060, REQ-064
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--gamma=1"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--gamma=a,b"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--gamma=0,1"]) == 1


def test_dng2hdr2jpg_rejects_invalid_postprocess_values(tmp_path):
    """
    @brief Validate postprocess and JPEG-compression parser rejections.
    @details Provides malformed or out-of-range values for postprocess options
      and asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060, REQ-065, REQ-073
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--post-gamma=0"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--brightness=foo"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--contrast=-1"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--saturation=0"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--jpg-compression=200"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--jpg-compression=bad"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--wow=1"]) == 1


def test_dng2hdr2jpg_rejects_missing_and_unknown_wow_mode(tmp_path):
    """
    @brief Validate wow mode parser rejects missing and unknown values.
    @details Exercises `--wow` token without value and with unsupported mode
      selector and asserts deterministic parse failures.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-073, REQ-075
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--wow"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--wow", "Unknown"]) == 1


def test_dng2hdr2jpg_applies_custom_gamma_value(monkeypatch, tmp_path):
    """
    @brief Validate custom gamma option is propagated to RAW postprocess calls.
    @details Runs default backend with `--gamma=1,1` and verifies all bracket
      extraction calls receive the selected gamma pair.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-060, REQ-064
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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--gamma=1,1"])

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
        if command and command[0] == "magick":
            Path(command[-1]).write_text("magick", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
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
    @satisfies TST-011, REQ-059, REQ-060
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda _cmd: None)

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse"]) == 1


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


def test_dng2hdr2jpg_wow_uses_convert_when_magick_is_missing(monkeypatch, tmp_path):
    """
    @brief Reproduce wow dependency bug when only `convert` binary is available.
    @details Configures dependency lookup so `magick` is missing but `convert`
      exists; expected behavior is successful wow execution path for backward-
      compatible ImageMagick CLI naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059, REQ-073
    """

    observed = {"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for wow dependency fallback test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for wow dependency fallback test."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder files."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return merged/wow payload compatible with encode path."""

            name = Path(path).name
            if name in {"merged_hdr.tif", "wow_output.tif"}:
                return _FakeImage16()
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Emulate successful backend and wow subprocess executions."""

        assert check is True
        if command and command[0] == "enfuse":
            output_flag = next(token for token in command if token.startswith("--output="))
            Path(output_flag.split("=", 1)[1]).write_text("merged", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        if command and command[0] == "convert":
            Path(command[-1]).write_text("wow", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )

    def _fake_which(cmd):
        """@brief Provide selective executable discovery for fallback reproducer."""

        if cmd == "enfuse":
            return "/usr/bin/enfuse"
        if cmd == "convert":
            return "/usr/bin/convert"
        return None

    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", _fake_which)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--wow", "ImageMagick"])

    assert result == 0
    assert output_jpg.exists()


def test_dng2hdr2jpg_fails_when_wow_opencv_dependencies_are_missing(monkeypatch, tmp_path):
    """
    @brief Validate OpenCV wow mode fails when Python dependencies are missing.
    @details Enables wow with `OpenCV`, forces dependency resolver failure, and
      asserts deterministic command failure without processing.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059, REQ-073, REQ-075
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg, "_resolve_wow_opencv_dependencies", lambda: None)

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--wow", "OpenCV"])

    assert result == 1


def test_dng2hdr2jpg_rejects_luminance_options_without_enable(tmp_path):
    """
    @brief Validate luminance options require enable flag.
    @details Uses luminance option selectors without backend enable flag and
      asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060, REQ-061, REQ-067
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--luminance-tmo=fattal"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--luminance-hdr-model=robertson"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--tmoR05Brightness=0"]) == 1


def test_dng2hdr2jpg_rejects_malformed_luminance_options(monkeypatch, tmp_path):
    """
    @brief Validate malformed luminance options are rejected.
    @details Provides empty luminance selector values and malformed `--tmo*`
      passthrough values and asserts deterministic parse failure.
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
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance", "--tmoR05Brightness"]) == 1
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-luminance", "--tmoR05Chroma="]) == 1
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-luminance", "--tmoR05Lightness", "--invalid"]
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
    @details Parses `pyproject.toml` and asserts that `rawpy`, `imageio`,
      `pillow`, `numpy`, and `opencv-python`
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
    assert any(dep.startswith("numpy") for dep in dependencies)
    assert any(dep.startswith("opencv-python") for dep in dependencies)


def test_dng2hdr2jpg_copies_dng_exif_and_sets_jpg_timestamps(monkeypatch, tmp_path):
    """
    @brief Validate EXIF propagation and filesystem timestamp synchronization.
    @details Runs enfuse flow with fake source DNG EXIF container and verifies
      copied EXIF payload is passed to JPEG save plus `os.utime` receives EXIF
      timestamp derived from `DateTimeOriginal`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-074
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "writes": [],
        "enfuse_cmd": None,
        "jpg_save": None,
        "utime_calls": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for EXIF/timestamp propagation test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for bracket and merged image flow."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic intermediate image artifact."""

            observed["writes"].append(Path(path).name)
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake uint16 payload consumed by encoder."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    class _FakeExif:
        """@brief Provide fake EXIF mapping compatible with production extraction."""

        def __init__(self):
            self._values = {
                36867: "2024:07:08 09:10:11",
            }

        def get(self, key):
            """@brief Return EXIF value for requested tag key."""

            return self._values.get(key)

        def tobytes(self):
            """@brief Return serialized EXIF payload marker."""

            return b"fake-exif-payload"

    class _FakeDngImage:
        """@brief Provide fake source DNG image object exposing `getexif`."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        @staticmethod
        def getexif():
            return _FakeExif()

    class _FakePilImage:
        """@brief Provide fake Pillow image object for JPG encode assertions."""

        def __init__(self, payload):
            self.mode = getattr(payload, "mode", "RGB")

        @staticmethod
        def getbands():
            return ("R", "G", "B")

        def point(self, _lut):
            return self

        def convert(self, target_mode):
            self.mode = target_mode
            return self

        def save(self, path, format, quality=None, optimize=None, exif=None, compress_level=None):
            del compress_level
            observed["jpg_save"] = {
                "path": str(path),
                "format": format,
                "quality": quality,
                "optimize": optimize,
                "exif": exif,
            }
            Path(path).write_text("jpg", encoding="utf-8")

    class _FakePilImageModule:
        """@brief Provide fake PIL Image module with `open` and `fromarray`."""

        @staticmethod
        def open(path):
            assert Path(path).suffix.lower() == ".dng"
            return _FakeDngImage()

        @staticmethod
        def fromarray(payload):
            return _FakePilImage(payload)

    class _FakeEnhancer:
        """@brief No-op enhancer preserving image identity."""

        def __init__(self, image):
            self._image = image

        def enhance(self, _value):
            return self._image

    class _FakePilEnhanceModule:
        """@brief Provide fake Pillow ImageEnhance module surface."""

        @staticmethod
        def Brightness(image):
            return _FakeEnhancer(image)

        @staticmethod
        def Contrast(image):
            return _FakeEnhancer(image)

        @staticmethod
        def Color(image):
            return _FakeEnhancer(image)

    def _fake_subprocess_run(command, check):
        """@brief Capture enfuse invocation and materialize merged TIFF output."""

        assert check is True
        observed["enfuse_cmd"] = command
        output_flag = next(token for token in command if token.startswith("--output="))
        merged_path = Path(output_flag.split("=", 1)[1])
        merged_path.write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def _fake_utime(path, times):
        """@brief Capture filesystem timestamp synchronization call."""

        observed["utime_calls"].append((Path(path), times))

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: (_FakeRawPyModule, _FakeImageIoModule, _FakePilImageModule, _FakePilEnhanceModule),
    )
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg.os, "utime", _fake_utime)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse"])

    assert result == 0
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["exif"] == b"fake-exif-payload"
    assert len(observed["utime_calls"]) == 1
    utime_path, utime_values = observed["utime_calls"][0]
    assert utime_path == output_jpg
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp("2024:07:08 09:10:11")
    assert utime_values == (expected_timestamp, expected_timestamp)


def test_dng2hdr2jpg_skips_timestamp_update_when_exif_datetime_missing(monkeypatch, tmp_path):
    """
    @brief Validate no timestamp update when EXIF datetime fields are absent.
    @details Runs enfuse flow with EXIF payload but without supported datetime
      tags and asserts JPEG EXIF copy remains active while `os.utime` is not
      called.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-074
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "utime_calls": [],
        "jpg_save": None,
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for missing-datetime EXIF test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for missing-datetime EXIF test."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    class _FakeExifNoDate:
        """@brief Provide fake EXIF payload without supported datetime tags."""

        @staticmethod
        def get(_key):
            return None

        @staticmethod
        def tobytes():
            return b"fake-exif-no-date"

    class _FakeDngImage:
        """@brief Provide fake source DNG image for missing datetime test."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        @staticmethod
        def getexif():
            return _FakeExifNoDate()

    class _FakePilImage:
        """@brief Provide fake PIL image object for final JPEG save assertions."""

        mode = "RGB"

        @staticmethod
        def getbands():
            return ("R", "G", "B")

        def point(self, _lut):
            return self

        def convert(self, _target_mode):
            return self

        def save(self, path, format, quality=None, optimize=None, exif=None, compress_level=None):
            del quality, optimize, compress_level
            observed["jpg_save"] = {"format": format, "exif": exif}
            Path(path).write_text("jpg", encoding="utf-8")

    class _FakePilImageModule:
        """@brief Provide fake PIL Image module with DNG open capability."""

        @staticmethod
        def open(path):
            assert Path(path).suffix.lower() == ".dng"
            return _FakeDngImage()

        @staticmethod
        def fromarray(_payload):
            return _FakePilImage()

    class _FakeEnhancer:
        """@brief No-op enhancer helper."""

        def __init__(self, image):
            self._image = image

        def enhance(self, _value):
            return self._image

    class _FakePilEnhanceModule:
        """@brief Provide fake ImageEnhance module for shared postprocess path."""

        @staticmethod
        def Brightness(image):
            return _FakeEnhancer(image)

        @staticmethod
        def Contrast(image):
            return _FakeEnhancer(image)

        @staticmethod
        def Color(image):
            return _FakeEnhancer(image)

    def _fake_subprocess_run(command, check):
        assert check is True
        output_flag = next(token for token in command if token.startswith("--output="))
        Path(output_flag.split("=", 1)[1]).write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def _fake_utime(path, times):
        observed["utime_calls"].append((Path(path), times))

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: (_FakeRawPyModule, _FakeImageIoModule, _FakePilImageModule, _FakePilEnhanceModule),
    )
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg.os, "utime", _fake_utime)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse"])

    assert result == 0
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["exif"] == b"fake-exif-no-date"
    assert observed["utime_calls"] == []


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
    @satisfies TST-011, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073
    """

    dng2hdr2jpg.print_help("0.0.0")
    captured = capsys.readouterr()
    output = captured.out
    operators_section = output.split("  Luminance operators:", 1)[1].split(
        "  Luminance operator main CLI controls:", 1
    )[0]

    assert "--enable-luminance" in output
    assert "--enable-enfuse" in output
    assert "--gamma=<a,b>" in output
    assert "--post-gamma=<value>" in output
    assert "--brightness=<value>" in output
    assert "--contrast=<value>" in output
    assert "--saturation=<value>" in output
    assert "--jpg-compression=<0..100>" in output
    assert "--wow" in output
    assert "--luminance-hdr-model=<name>" in output
    assert "--luminance-hdr-weight=<name>" in output
    assert "--luminance-hdr-response-curve=<name>" in output
    assert "--luminance-tmo=<name>" in output
    assert "default: reinhard02" in output
    assert "Luminance operators:" in output
    assert "Luminance operator main CLI controls:" in output
    assert "┌" in output and "┬" in output and "┐" in output
    assert "├" in output and "┼" in output and "┤" in output
    assert "└" in output and "┴" in output and "┘" in output
    assert "┬──┬" not in operators_section
    assert "┼──┼" not in operators_section
    assert "│ Operator" in output
    assert operators_section.count("│ Operator") == 1
    assert "│ Neutrality" in output and "│ When to use" in output
    assert "`reinhard02`" in output
    assert "`mantiuk08`" in output
    assert "│ Medium" in output
    assert "│ Natural-looking local adaptation with preserved detail" in output
    assert "`--tmoR02Key`" in output
    assert "`--tmoM08ColorSaturation`" in output
    assert "--tmo* <value> | --tmo*=<value>" in output
    assert "mutually exclusive with --enable-luminance" in output


def test_dng2hdr2jpg_applies_postprocess_controls_and_quality_mapping(tmp_path):
    """
    @brief Validate shared postprocess controls and JPEG quality mapping.
    @details Executes encode path with non-default gamma/brightness/contrast/
      saturation factors and verifies fake Pillow operations and quality value.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066, REQ-073
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


def test_dng2hdr2jpg_applies_wow_pipeline_only_when_enabled(monkeypatch, tmp_path):
    """
    @brief Validate wow-stage execution only when explicitly enabled.
    @details Executes encode path with `wow_mode="ImageMagick"`, captures ImageMagick
      command vectors, and verifies two-step wow flow over temporary files
      (`postprocessed_input.tif` then `wow_output.tif`) before final JPEG save.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066, REQ-073
    """

    observed = {"commands": [], "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for wow encode assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake payload for merged/wow TIFF paths."""

            if Path(path).name == "wow_output.tif":
                class _FakeWowPayload:
                    mode = "RGB"

                return _FakeWowPayload()
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture wow subprocess calls and materialize outputs."""

        assert check is True
        observed["commands"].append(command)
        if command and command[0] == "magick":
            Path(command[-1]).write_text("artifact", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_resolve_imagemagick_command", lambda: "magick")

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
            wow_mode="ImageMagick",
        ),
    )

    assert len(observed["commands"]) == 2
    assert observed["commands"][0][0] == "magick"
    assert observed["commands"][1][0] == "magick"
    assert Path(observed["commands"][0][-1]).name == "wow_input_16.tif"
    assert Path(observed["commands"][1][-1]).name == "wow_output.tif"
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_applies_opencv_wow_pipeline_when_selected(monkeypatch, tmp_path):
    """
    @brief Validate OpenCV wow-stage dispatch when wow mode is `OpenCV`.
    @details Executes encode path with `wow_mode="OpenCV"`, injects fake OpenCV
      dependency tuple, and verifies OpenCV wow function receives expected
      temporary input/output TIFF paths before final JPEG save.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-073, REQ-075
    """

    observed = {"opencv_call": {}, "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for OpenCV wow dispatch test."""

        @staticmethod
        def imread(path):
            """@brief Return fake payload for merged/wow TIFF reads."""

            if Path(path).name == "wow_output.tif":
                class _FakeWowPayload:
                    mode = "RGB"

                return _FakeWowPayload()
            return _FakeImage16()

    def _fake_apply_validated_wow_pipeline_opencv(input_file, output_file, cv2_module, np_module):
        """@brief Capture OpenCV wow dispatch parameters and materialize output."""

        observed["opencv_call"] = {
            "input": Path(input_file).name,
            "output": Path(output_file).name,
            "cv2": cv2_module,
            "np": np_module,
        }
        Path(output_file).write_text("wow", encoding="utf-8")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_apply_validated_wow_pipeline_opencv",
        _fake_apply_validated_wow_pipeline_opencv,
    )

    merged_tiff = tmp_path / "merged_hdr.tif"
    merged_tiff.write_text("merged", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)
    fake_cv2_module = object()
    fake_numpy_module = object()

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
            wow_mode="OpenCV",
        ),
        wow_opencv_dependencies=(fake_cv2_module, fake_numpy_module),
    )

    assert observed["opencv_call"] is not None
    assert observed["opencv_call"]["input"] == "postprocessed_input.tif"
    assert observed["opencv_call"]["output"] == "wow_output.tif"
    assert observed["opencv_call"]["cv2"] is fake_cv2_module
    assert observed["opencv_call"]["np"] is fake_numpy_module
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_opencv_wow_accepts_uint8_input_by_upconverting(tmp_path):
    """
    @brief Reproduce OpenCV wow failure when wow input TIFF is decoded as uint8.
    @details Executes `_apply_validated_wow_pipeline_opencv` with fake cv2 read
      path returning `uint8` 3-channel image and expects deterministic in-function
      promotion to `uint16` before float-domain pipeline execution.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-073, REQ-075
    """

    numpy_module = __import__("numpy")

    class _FakeCv2Module:
        """@brief Provide minimal cv2 surface for uint8 OpenCV wow reproducer."""

        IMREAD_UNCHANGED = -1
        COLOR_BGR2RGB = 10
        COLOR_RGB2BGR = 11
        BORDER_REFLECT = 12

        def __init__(self):
            self.written = None

        def imread(self, path, mode):
            """@brief Return deterministic uint8 wow input tensor."""

            del path
            assert mode == self.IMREAD_UNCHANGED
            return numpy_module.zeros((2, 2, 3), dtype=numpy_module.uint8)

        @staticmethod
        def cvtColor(image, code):
            """@brief Return channel-reordered tensor for BGR/RGB conversions."""

            if code in (_FakeCv2Module.COLOR_BGR2RGB, _FakeCv2Module.COLOR_RGB2BGR):
                return image[..., ::-1]
            raise AssertionError(f"Unexpected conversion code: {code}")

        @staticmethod
        def GaussianBlur(image, ksize, sigmaX, sigmaY, borderType):
            """@brief Return deterministic no-op blur payload."""

            del ksize, sigmaX, sigmaY
            assert borderType == _FakeCv2Module.BORDER_REFLECT
            return image

        def imwrite(self, path, payload):
            """@brief Capture output tensor metadata and materialize artifact."""

            self.written = {
                "path": Path(path).name,
                "dtype": str(payload.dtype),
                "shape": payload.shape,
            }
            Path(path).write_text("wow-output", encoding="utf-8")
            return True

    input_tiff = tmp_path / "postprocessed_input.tif"
    input_tiff.write_text("payload", encoding="utf-8")
    output_tiff = tmp_path / "wow_output.tif"
    fake_cv2_module = _FakeCv2Module()

    dng2hdr2jpg._apply_validated_wow_pipeline_opencv(
        input_file=input_tiff,
        output_file=output_tiff,
        cv2_module=fake_cv2_module,
        np_module=numpy_module,
    )

    assert fake_cv2_module.written is not None
    assert fake_cv2_module.written["path"] == "wow_output.tif"
    assert fake_cv2_module.written["dtype"] == "uint16"
    assert fake_cv2_module.written["shape"] == (2, 2, 3)
    assert output_tiff.exists()


def test_dng2hdr2jpg_wow_uint16_output_is_normalized_before_fromarray(monkeypatch, tmp_path):
    """
    @brief Reproduce wow-path crash when ImageMagick output is uint16 RGB payload.
    @details Simulates wow output decode as `uint16` data and enforces a strict
      fake `Image.fromarray` contract that rejects non-`uint8` payload, matching
      observed Pillow failure; expected behavior is successful normalization before
      `fromarray`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-058, REQ-066, REQ-073
    """

    observed = {"jpg_save": None, "commands": []}

    class _FakeWowScaled:
        """@brief Provide clip/astype chain for wow uint16 normalization."""

        def clip(self, _low, _high):
            """@brief Return self for deterministic clipping chain."""

            return self

        def astype(self, dtype):
            """@brief Return uint8 payload marker after normalization."""

            assert dtype == "uint8"

            class _FakeWowUint8Payload:
                mode = "RGB"
                dtype = "uint8"

            return _FakeWowUint8Payload()

    class _FakeWowU16Payload:
        """@brief Emulate wow output payload with uint16 dtype."""

        dtype = "uint16"

        def __truediv__(self, value):
            """@brief Emulate normalization division branch."""

            assert value == 257.0
            return _FakeWowScaled()

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for wow uint16 reproducer."""

        @staticmethod
        def imread(path):
            """@brief Return base and wow payloads for encode path."""

            if Path(path).name == "merged_hdr.tif":
                class _BasePilPayload:
                    mode = "RGB"

                    def getbands(self):
                        return ("R", "G", "B")

                    def point(self, _lut):
                        return self

                    def convert(self, _mode):
                        return self

                    def save(
                        self,
                        save_path,
                        format,
                        quality=None,
                        optimize=None,
                        compress_level=None,
                        compression=None,
                        exif=None,
                    ):
                        del quality, optimize, compress_level, compression, exif
                        Path(save_path).write_text(format.lower(), encoding="utf-8")

                return _BasePilPayload()
            if Path(path).name == "wow_output.tif":
                return _FakeWowU16Payload()
            return _FakeImage16()

    class _StrictPilImageModule:
        """@brief Fake PIL module that fails on non-uint8 fromarray payload."""

        @staticmethod
        def fromarray(payload):
            """@brief Enforce uint8-only conversion to reproduce original crash."""

            if getattr(payload, "dtype", None) != "uint8":
                raise TypeError(f"Cannot handle this data type: {getattr(payload, 'dtype', None)}")
            class _FakePilImage:
                mode = "RGB"

                def getbands(self):
                    return ("R", "G", "B")

                def point(self, _lut):
                    return self

                def convert(self, _mode):
                    return self

                def save(
                    self,
                    path,
                    format,
                    quality=None,
                    optimize=None,
                    compress_level=None,
                    compression=None,
                    exif=None,
                ):
                    del quality, optimize, compress_level, compression, exif
                    observed["jpg_save"] = {"format": format}
                    Path(path).write_text("jpg", encoding="utf-8")

            return _FakePilImage()

    class _FakePilEnhanceModule:
        """@brief No-op ImageEnhance replacement."""

        @staticmethod
        def Brightness(image):
            class _E:
                def enhance(self, _v):
                    return image
            return _E()

        @staticmethod
        def Contrast(image):
            class _E:
                def enhance(self, _v):
                    return image
            return _E()

        @staticmethod
        def Color(image):
            class _E:
                def enhance(self, _v):
                    return image
            return _E()

    def _fake_subprocess_run(command, check):
        """@brief Emulate successful wow subprocess output materialization."""

        assert check is True
        observed["commands"].append(command)
        if command and command[0] == "magick":
            Path(command[-1]).write_text("artifact", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_resolve_imagemagick_command", lambda: "magick")

    merged_tiff = tmp_path / "merged_hdr.tif"
    merged_tiff.write_text("merged", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    dng2hdr2jpg._encode_jpg(
        imageio_module=_FakeImageIoModule,
        pil_image_module=_StrictPilImageModule,
        pil_enhance_module=_FakePilEnhanceModule,
        merged_tiff=merged_tiff,
        output_jpg=output_jpg,
        postprocess_options=dng2hdr2jpg.PostprocessOptions(
            post_gamma=1.0,
            brightness=1.0,
            contrast=1.0,
            saturation=1.0,
            jpg_compression=10,
            wow_mode="ImageMagick",
        ),
    )

    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()
