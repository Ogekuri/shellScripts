"""
@brief Validate `dng2hdr2jpg` command EV parsing and HDR merge contract.
@details Verifies argument validation, EV parsing/default behavior, three-
  bracket extraction multipliers, dual-backend HDR merge behavior, shared
  postprocessing options, and temporary artifact cleanup semantics.
@satisfies TST-011, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075, REQ-076, REQ-077
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
    @return {tuple[type, type, type, type, object, object]} Fake dependency tuple with cv2/numpy placeholders.
    """

    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)
    return raw_module, imageio_module, pil_image_module, pil_enhance_module, object(), object()


def _patch_processing_pipeline(monkeypatch, observed):
    """@brief Patch 16-bit processing helpers for deterministic run tests.

    @details Replaces `_read_u16_image`, `_apply_postprocess_16bit`, and
      `_magic_retouch` with low-overhead fakes that preserve pipeline ordering
      and option capture without numpy/opencv runtime dependencies.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param observed {dict[str, object]} Shared mutable assertion map.
    @return {None} Side effects only.
    """

    def _fake_read_u16_image(imageio_module, np_module, merged_tiff):
        """@brief Record read stage and return deterministic fake uint16 payload."""

        del imageio_module, np_module
        observed.setdefault("pipeline", []).append(("read_u16", Path(merged_tiff).name))
        return _FakeImage16()

    def _fake_apply_postprocess(np_module, cv2_module, image_u16, postprocess_options):
        """@brief Record postprocess stage options and return unchanged payload."""

        del np_module, cv2_module
        observed.setdefault("pipeline", []).append(
            (
                "postprocess",
                postprocess_options.post_gamma,
                postprocess_options.brightness,
                postprocess_options.contrast,
                postprocess_options.saturation,
            )
        )
        return image_u16

    def _fake_magic_retouch(np_module, cv2_module, image_u16, magic_options):
        """@brief Record magic-retouch stage invocation and return unchanged payload."""

        del np_module, cv2_module
        observed.setdefault("pipeline", []).append(("magic", magic_options.enabled))
        return image_u16

    monkeypatch.setattr(dng2hdr2jpg, "_read_u16_image", _fake_read_u16_image)
    monkeypatch.setattr(dng2hdr2jpg, "_apply_postprocess_16bit", _fake_apply_postprocess)
    monkeypatch.setattr(dng2hdr2jpg, "_magic_retouch", _fake_magic_retouch)


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
    _patch_processing_pipeline(monkeypatch, observed)

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
    assert ("read_u16", "merged_hdr.tif") in observed["pipeline"]
    assert ("postprocess", 1.0, 1.0, 1.0, 1.0) in observed["pipeline"]
    assert not any(stage[0] == "magic" for stage in observed["pipeline"])
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
    _patch_processing_pipeline(monkeypatch, observed)

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
    assert ("postprocess", 1.0, 1.25, 0.85, 0.55) in observed["pipeline"]
    assert not any(stage[0] == "magic" for stage in observed["pipeline"])
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
    _patch_processing_pipeline(monkeypatch, observed)

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
    _patch_processing_pipeline(monkeypatch, observed)

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
    assert ("postprocess", 1.0, 1.0, 1.0, 1.0) in observed["pipeline"]


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
    _patch_processing_pipeline(monkeypatch, observed)

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
    @satisfies TST-011, REQ-060, REQ-065
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


def test_dng2hdr2jpg_rejects_invalid_magic_options(tmp_path):
    """
    @brief Validate magic-retouch option parser rejects malformed values.
    @details Provides malformed values for adaptive magic-retouch controls and
      removed legacy options and asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-073
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-denoise-strength=-0.1"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-denoise-strength=1.5"]
        )
        == 1
    )
    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-gamma-bias=0.8"]) == 1
    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-vibrance-strength=1.5"])
        == 1
    )
    assert dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-sharpen-strength=2"]
    ) == 1
    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-filter=legacy"]) == 1
    )
    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-kernel-size=4"]) == 1
    )
    assert dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-color-balance-strength=-0.1"]
    ) == 1


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
    _patch_processing_pipeline(monkeypatch, observed)

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
    _patch_processing_pipeline(monkeypatch, observed)

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
      `pillow`, `opencv-python`, and `numpy`
      are declared in `project.dependencies` so uv tool installs provide command
      runtime requirements without manual post-install steps.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059, REQ-077
    """

    project_root = Path(__file__).resolve().parents[1]
    pyproject_path = project_root / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = pyproject_data["project"].get("dependencies", [])

    assert any(dep.startswith("rawpy") for dep in dependencies)
    assert any(dep.startswith("imageio") for dep in dependencies)
    assert any(dep.startswith("pillow") for dep in dependencies)
    assert any(dep.startswith("opencv-python") for dep in dependencies)
    assert any(dep.startswith("numpy") for dep in dependencies)


def test_dng2hdr2jpg_handles_rgba_merged_image_for_jpeg_output(tmp_path):
    """
    @brief Validate JPG encode path strips alpha channel before final write.
    @details Simulates in-memory payload that resolves to RGBA mode and asserts
      conversion to RGB before JPEG save.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066
    """

    observed = {"jpg_save": None}

    class _FakeRgbaPayload:
        """@brief Fake payload that preserves RGBA mode through conversion chain."""

        mode = "RGBA"

        def __truediv__(self, _value):
            """@brief Return self for scaling operation."""

            return self

        def clip(self, _low, _high):
            """@brief Return self for clipping operation."""

            return self

        def astype(self, _dtype):
            """@brief Return self to preserve RGBA mode on cast."""

            return self

    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, _ = _build_fake_pillow_modules(observed)

    dng2hdr2jpg._encode_jpg(
        pil_image_module=pil_image_module,
        image_u16=_FakeRgbaPayload(),
        output_jpg=output_jpg,
        jpg_compression=10,
    )

    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["mode"] == "RGB"
    assert output_jpg.exists()


def test_dng2hdr2jpg_help_includes_luminance_options(capsys):
    """
    @brief Validate command help documents luminance backend options.
    @details Calls help renderer and asserts presence of luminance enable flag,
      simplified luminance selectors, postprocess selectors, and magic-retouch controls.
    @param capsys {pytest.CaptureFixture[str]} Stdout/stderr capture fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-075
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
    assert "--magic-retouch" in output
    assert "--magic-denoise-strength=<0..1>" in output
    assert "--magic-gamma-bias=<value>" in output
    assert "--magic-clahe-clip-limit=<value>" in output
    assert "--magic-vibrance-strength=<0..1>" in output
    assert "--magic-sharpen-strength=<0..1>" in output
    assert "--magic-sharpen-threshold=<value>" in output
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
    @details Executes explicit postprocess stage with non-default
      gamma/brightness/contrast/saturation values and verifies deterministic
      stage execution on fake payload.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066, REQ-076
    """

    del tmp_path

    class _FakeNumpy:
        """@brief Fake numpy module for postprocess stage tests."""

        float32 = float
        uint16 = int

        @staticmethod
        def power(_x, _y):
            """@brief Return fake payload after gamma operation."""

            return _x

        @staticmethod
        def maximum(_x, _y):
            """@brief Return fake payload for clamp path."""

            return _x

        @staticmethod
        def clip(_x, _low, _high):
            """@brief Return fake payload for clipping paths."""

            return _x

        @staticmethod
        def rint(_x):
            """@brief Return fake payload for rounding path."""

            return _x

    class _FakeHsvChannel:
        """@brief Fake HSV channel supporting in-place scaling assignment."""

        def __mul__(self, _value):
            """@brief Keep fake channel unchanged for multiplication path."""

            return self

        def __imul__(self, _value):
            """@brief Keep fake channel unchanged."""

            return self

    class _FakeHsvImage:
        """@brief Fake HSV image supporting channel update contract."""

        def __getitem__(self, key):
            """@brief Return fake channel for saturation access."""

            assert key == (slice(None, None, None), slice(None, None, None), 1)
            return _FakeHsvChannel()

        def __setitem__(self, key, value):
            """@brief Accept saturation assignment contract."""

            del key, value

    class _FakeImagePayload:
        """@brief Fake uint16 payload with arithmetic hooks."""

        def astype(self, _dtype):
            """@brief Return self for dtype conversion."""

            return self

        def __truediv__(self, _other):
            """@brief Return self for normalized conversion."""

            return self

        def __mul__(self, _other):
            """@brief Return self for arithmetic operations."""

            return self

        def __sub__(self, _other):
            """@brief Return self for arithmetic operations."""

            return self

        def __add__(self, _other):
            """@brief Return self for arithmetic operations."""

            return self

    class _FakeCv2:
        """@brief Fake OpenCV module for saturation branch coverage."""

        COLOR_RGB2HSV = 1
        COLOR_HSV2RGB = 2

        @staticmethod
        def cvtColor(image, code):
            """@brief Return fake HSV or RGB payload for conversion steps."""

            if code == _FakeCv2.COLOR_RGB2HSV:
                del image
                return _FakeHsvImage()
            return _FakeImagePayload()

    output = dng2hdr2jpg._apply_postprocess_16bit(
        np_module=_FakeNumpy,
        cv2_module=_FakeCv2,
        image_u16=_FakeImagePayload(),
        postprocess_options=dng2hdr2jpg.PostprocessOptions(
            post_gamma=2.2,
            brightness=1.1,
            contrast=0.9,
            saturation=1.3,
            jpg_compression=80,
        ),
    )
    assert output is not None


def test_dng2hdr2jpg_runs_magic_retouch_stage_when_enabled(monkeypatch, tmp_path):
    """
    @brief Validate optional magic-retouch stage placement and activation.
    @details Executes full run with `--magic-retouch` and verifies stage order:
      read -> postprocess -> magic -> encode.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-074, REQ-076
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for magic stage ordering test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for bracket writes."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder files."""

            Path(path).write_text("payload", encoding="utf-8")

    def _fake_subprocess_run(command, check):
        """@brief Materialize merged tiff output for backend call."""

        assert check is True
        output_flag = next(token for token in command if token.startswith("--output="))
        Path(output_flag.split("=", 1)[1]).write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def _fake_encode_jpg(pil_image_module, image_u16, output_jpg, jpg_compression):
        """@brief Record encode stage and create output artifact."""

        del pil_image_module, image_u16
        observed.setdefault("pipeline", []).append(("encode", jpg_compression))
        Path(output_jpg).write_text("jpg", encoding="utf-8")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_encode_jpg", _fake_encode_jpg)
    _patch_processing_pipeline(monkeypatch, observed)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse", "--magic-retouch"])
    assert result == 0
    pipeline = observed["pipeline"]
    assert pipeline[0][0] == "read_u16"
    assert pipeline[1][0] == "postprocess"
    assert pipeline[2][0] == "magic"
    assert pipeline[3][0] == "encode"


def test_dng2hdr2jpg_encode_jpg_uses_jpg_compression_quality_mapping(tmp_path):
    """
    @brief Validate dedicated JPG encoding step maps compression to quality.
    @details Executes `_encode_jpg` with fake uint16 payload and checks quality
      conversion uses `100 - jpg_compression` clamped range.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066
    """

    observed = {"jpg_save": None}
    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, _ = _build_fake_pillow_modules(observed)

    dng2hdr2jpg._encode_jpg(
        pil_image_module=pil_image_module,
        image_u16=_FakeImage16(),
        output_jpg=output_jpg,
        jpg_compression=80,
    )

    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["quality"] == 20
    assert output_jpg.exists()


def test_dng2hdr2jpg_magic_retouch_does_not_collapse_luminance():
    """
    @brief Reproduce magic-retouch exposure-collapse defect on well-exposed input.
    @details Uses a constant well-exposed uint16 image and verifies magic-retouch
      output mean luminance remains in a bounded ratio against input mean.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-075, REQ-076
    """

    np_module = pytest.importorskip("numpy")
    cv2_module = pytest.importorskip("cv2")

    image_u16 = np_module.full((32, 32, 3), 40000, dtype=np_module.uint16)
    options = dng2hdr2jpg.MagicRetouchOptions(
        enabled=True,
        denoise_strength=dng2hdr2jpg.DEFAULT_MAGIC_DENOISE_STRENGTH,
        gamma_bias=dng2hdr2jpg.DEFAULT_MAGIC_GAMMA_BIAS,
        clahe_clip_limit=dng2hdr2jpg.DEFAULT_MAGIC_CLAHE_CLIP_LIMIT,
        vibrance_strength=dng2hdr2jpg.DEFAULT_MAGIC_VIBRANCE_STRENGTH,
        sharpen_strength=dng2hdr2jpg.DEFAULT_MAGIC_SHARPEN_STRENGTH,
        sharpen_threshold=dng2hdr2jpg.DEFAULT_MAGIC_SHARPEN_THRESHOLD,
    )

    output_u16 = dng2hdr2jpg._magic_retouch(np_module, cv2_module, image_u16, options)
    input_mean = float(image_u16.mean())
    output_mean = float(output_u16.mean())
    ratio = output_mean / input_mean

    assert ratio >= 0.70
    assert ratio <= 1.30


def test_dng2hdr2jpg_magic_retouch_preserves_shape_and_dtype_with_adaptive_flow():
    """
    @brief Validate adaptive magic-retouch preserves shape and uint16 domain.
    @details Runs `_magic_retouch` over deterministic uint16 payload with
      non-neutral adaptive controls and validates shape/dtype stability.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-075
    """

    np_module = pytest.importorskip("numpy")
    cv2_module = pytest.importorskip("cv2")

    image_u16 = np_module.full((24, 24, 3), 32000, dtype=np_module.uint16)
    options = dng2hdr2jpg.MagicRetouchOptions(
        enabled=True,
        denoise_strength=0.01,
        gamma_bias=0.08,
        clahe_clip_limit=1.2,
        vibrance_strength=0.2,
        sharpen_strength=0.25,
        sharpen_threshold=0.01,
    )
    output_u16 = dng2hdr2jpg._magic_retouch(np_module, cv2_module, image_u16, options)
    assert output_u16.shape == image_u16.shape
    assert output_u16.dtype == np_module.uint16


def test_dng2hdr2jpg_parses_new_magic_options_assignment_and_split(monkeypatch, tmp_path):
    """
    @brief Validate parser accepts new magic options in assignment and split forms.
    @details Executes full run with mixed assignment/split syntax and asserts
      parsed adaptive magic options are propagated to `_magic_retouch`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-073, REQ-078
    """

    observed = {"brights": [], "output_bps": [], "use_camera_wb": [], "no_auto_bright": [], "gamma": []}
    captured_magic_options = []
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for magic option parser test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for bracket writes."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder files."""

            Path(path).write_text("payload", encoding="utf-8")

    def _fake_subprocess_run(command, check):
        """@brief Materialize merged tiff output for backend call."""

        assert check is True
        output_flag = next(token for token in command if token.startswith("--output="))
        Path(output_flag.split("=", 1)[1]).write_text("merged", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def _fake_magic_retouch(np_module, cv2_module, image_u16, magic_options):
        """@brief Capture magic options propagated after parse stage."""

        del np_module, cv2_module
        captured_magic_options.append(magic_options)
        return image_u16

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(_FakeRawPyModule, _FakeImageIoModule, observed),
    )
    monkeypatch.setattr(dng2hdr2jpg.shutil, "which", lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None)
    _patch_processing_pipeline(monkeypatch, observed)
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_magic_retouch", _fake_magic_retouch)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-enfuse",
            "--magic-retouch",
            "--magic-denoise-strength=0.08",
            "--magic-gamma-bias",
            "0.1",
            "--magic-clahe-clip-limit=1.5",
            "--magic-vibrance-strength",
            "0.2",
            "--magic-sharpen-strength",
            "0.4",
            "--magic-sharpen-threshold",
            "0.015",
        ]
    )
    assert result == 0
    assert captured_magic_options
    magic_options = captured_magic_options[0]
    assert isinstance(magic_options, dng2hdr2jpg.MagicRetouchOptions)
    assert magic_options.denoise_strength == pytest.approx(0.08)
    assert magic_options.gamma_bias == pytest.approx(0.1)
    assert magic_options.clahe_clip_limit == pytest.approx(1.5)
    assert magic_options.vibrance_strength == pytest.approx(0.2)
    assert magic_options.sharpen_strength == pytest.approx(0.4)
    assert magic_options.sharpen_threshold == pytest.approx(0.015)


def test_dng2hdr2jpg_magic_retouch_defaults_are_noise_conservative():
    """
    @brief Validate default magic-retouch parameters are configured for neutral output.
    @details Asserts defaults target a low-impact baseline profile with neutral
      adaptive controls and zero sharpen blend.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-073, REQ-075
    """

    assert dng2hdr2jpg.DEFAULT_MAGIC_DENOISE_STRENGTH == pytest.approx(0.0)
    assert dng2hdr2jpg.DEFAULT_MAGIC_GAMMA_BIAS == pytest.approx(0.0)
    assert dng2hdr2jpg.DEFAULT_MAGIC_CLAHE_CLIP_LIMIT == pytest.approx(0.0)
    assert dng2hdr2jpg.DEFAULT_MAGIC_VIBRANCE_STRENGTH == pytest.approx(0.0)
    assert dng2hdr2jpg.DEFAULT_MAGIC_SHARPEN_STRENGTH == pytest.approx(0.0)
    assert dng2hdr2jpg.DEFAULT_MAGIC_SHARPEN_THRESHOLD == pytest.approx(0.02)


def test_dng2hdr2jpg_magic_retouch_bypasses_zero_controlled_stages(monkeypatch):
    """
    @brief Validate zero-valued controls bypass adaptive stage computations.
    @details Injects strict fakes and verifies denoise, gamma-bias, vibrance,
      and sharpen computations are not executed when their controls are `0`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-075
    """

    np_module = pytest.importorskip("numpy")
    cv2_module = pytest.importorskip("cv2")
    image_u16 = np_module.full((16, 16, 3), 30000, dtype=np_module.uint16)
    options = dng2hdr2jpg.MagicRetouchOptions(
        enabled=True,
        denoise_strength=0.0,
        gamma_bias=0.0,
        clahe_clip_limit=0.0,
        vibrance_strength=0.0,
        sharpen_strength=0.0,
        sharpen_threshold=0.02,
    )
    observed = {
        "gray_calls": 0,
        "gaussian_gray_calls": 0,
        "gaussian_sharp_calls": 0,
        "median_calls": 0,
        "hsv_calls": 0,
        "power_calls": 0,
    }
    original_cvt_color = cv2_module.cvtColor
    original_gaussian = cv2_module.GaussianBlur
    original_median = cv2_module.medianBlur
    original_power = np_module.power

    def _guard_cvt_color(image, code):
        """@brief Track color conversions used by adaptive stages."""

        if code == cv2_module.COLOR_RGB2GRAY:
            observed["gray_calls"] += 1
            return original_cvt_color(image, code)
        if code == cv2_module.COLOR_RGB2HSV:
            observed["hsv_calls"] += 1
        return original_cvt_color(image, code)

    def _guard_gaussian(image, ksize, sigma, *args, **kwargs):
        """@brief Track Gaussian calls by payload dimensionality."""

        if getattr(image, "ndim", 0) == 2:
            observed["gaussian_gray_calls"] += 1
        else:
            observed["gaussian_sharp_calls"] += 1
        return original_gaussian(image, ksize, sigma, *args, **kwargs)

    def _guard_median(image, ksize):
        """@brief Track median calls used by denoise stage."""

        observed["median_calls"] += 1
        return original_median(image, ksize)

    def _guard_power(base, exponent, *args, **kwargs):
        """@brief Track gamma correction power calls."""

        observed["power_calls"] += 1
        return original_power(base, exponent, *args, **kwargs)

    monkeypatch.setattr(cv2_module, "cvtColor", _guard_cvt_color)
    monkeypatch.setattr(cv2_module, "GaussianBlur", _guard_gaussian)
    monkeypatch.setattr(cv2_module, "medianBlur", _guard_median)
    monkeypatch.setattr(np_module, "power", _guard_power)

    output_u16 = dng2hdr2jpg._magic_retouch(np_module, cv2_module, image_u16, options)

    assert output_u16.shape == image_u16.shape
    assert output_u16.dtype == np_module.uint16
    assert observed["gray_calls"] == 0
    assert observed["gaussian_gray_calls"] == 0
    assert observed["gaussian_sharp_calls"] == 0
    assert observed["median_calls"] == 0
    assert observed["hsv_calls"] == 0
    assert observed["power_calls"] == 0


def test_dng2hdr2jpg_magic_retouch_applies_denoise_when_strength_is_positive(monkeypatch):
    """
    @brief Validate denoise stage executes deterministically when strength is positive.
    @details Tracks Gaussian calls and verifies denoise stage is executed when
      `denoise_strength>0` even on low-noise constant payloads.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-075
    """

    np_module = pytest.importorskip("numpy")
    cv2_module = pytest.importorskip("cv2")
    image_u16 = np_module.full((16, 16, 3), 30000, dtype=np_module.uint16)
    options = dng2hdr2jpg.MagicRetouchOptions(
        enabled=True,
        denoise_strength=0.25,
        gamma_bias=0.0,
        clahe_clip_limit=0.0,
        vibrance_strength=0.0,
        sharpen_strength=0.0,
        sharpen_threshold=0.02,
    )
    observed = {"gaussian_calls": 0}
    original_gaussian = cv2_module.GaussianBlur

    def _guard_gaussian(image, ksize, sigma_x=0, sigma_y=0, *args, **kwargs):
        """@brief Track Gaussian calls used by deterministic denoise stage."""

        observed["gaussian_calls"] += 1
        return original_gaussian(image, ksize, sigma_x, sigma_y, *args, **kwargs)

    monkeypatch.setattr(cv2_module, "GaussianBlur", _guard_gaussian)
    output_u16 = dng2hdr2jpg._magic_retouch(np_module, cv2_module, image_u16, options)

    assert output_u16.shape == image_u16.shape
    assert output_u16.dtype == np_module.uint16
    assert observed["gaussian_calls"] == 1
