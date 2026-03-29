"""
@brief Validate `dng2hdr2jpg` command EV parsing and HDR merge contract.
@details Verifies argument validation, static/adaptive EV selector behavior,
  three-bracket extraction multipliers, dual-backend HDR merge behavior,
  shared postprocessing options, and temporary artifact cleanup semantics.
    @satisfies TST-011, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075, REQ-077, REQ-078, REQ-079, REQ-080, REQ-081, REQ-082, REQ-083, REQ-084, REQ-085, REQ-086, REQ-087, REQ-088, REQ-089, REQ-090, REQ-091, REQ-092, REQ-093, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099
@return {None} Pytest module scope.
"""

from pathlib import Path
from importlib import import_module
import sys
import struct
import subprocess
import tempfile as std_tempfile
import tomllib
import warnings

import pytest

PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

for module_name in (
    "shell_scripts.commands.dng2hdr2jpg",
    "shell_scripts.commands",
    "shell_scripts",
):
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

    def postprocess(
        self, bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
    ):
        """@brief Capture bracket extraction options and return payload marker.

        @param bright {float} Brightness multiplier.
        @param output_bps {int} Output bit depth.
        @param use_camera_wb {bool} Camera white-balance enable flag.
        @param no_auto_bright {bool} Auto-bright disable flag.
        @param gamma {tuple[float, float]} Raw gamma pair.
        @param user_flip {int|None} rawpy orientation override selector.
        @return {str} Deterministic payload marker.
        """

        self._observed["brights"].append(bright)
        self._observed["output_bps"].append(output_bps)
        self._observed["use_camera_wb"].append(use_camera_wb)
        self._observed["no_auto_bright"].append(no_auto_bright)
        self._observed["gamma"].append(gamma)
        self._observed.setdefault("user_flip", []).append(user_flip)
        return f"rgb-{bright}"

    @property
    def white_level(self) -> int:
        """@brief Return deterministic white level used for bit-depth detection.

        @return {int} White-level scalar representing 14-bit RAW range.
        """

        return 16383


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

    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-enfuse", "--ev=3.25"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-enfuse", "--ev=0.2"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--enable-enfuse", "--ev", "bad"]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_missing_or_duplicated_backend_selector(tmp_path):
    """
    @brief Validate backend selector exclusivity and requiredness.
    @details Verifies parser rejects calls without backend selector and calls
      with both backend selectors together.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-060
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=1"]) == 1
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--enable-luminance",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_missing_or_duplicated_exposure_selector(tmp_path):
    """
    @brief Validate exposure selector requiredness and exclusivity.
    @details Verifies parser rejects calls without exposure selector and calls
      with both `--ev` and `--auto-ev` selectors together.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--enable-enfuse"]) == 1
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--auto-ev",
                "--enable-enfuse",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_invalid_auto_ev_value(tmp_path):
    """
    @brief Validate `--auto-ev` parser rejects unsupported values.
    @details Provides unsupported `--auto-ev` assignment value while keeping
      backend and positional arguments valid.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--auto-ev=maybe", "--enable-enfuse"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--auto-ev=false", "--enable-enfuse"]
        )
        == 1
    )


def test_detect_dng_bits_per_color_prefers_raw_container_bit_depth():
    """
    @brief Validate DNG bit-depth detection prefers RAW sample container depth.
    @details Reproduces a DNG metadata profile where `white_level` indicates
      effective sensor dynamic range (`4000`, ~12 bits) while RAW sample storage
      uses 16-bit container depth. Asserts detector returns container depth.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-092, REQ-093
    """

    class _FakeDtype:
        """@brief Provide deterministic dtype stub with 16-bit itemsize."""

        itemsize = 2

    class _FakeRawImage:
        """@brief Provide deterministic RAW image stub with dtype metadata."""

        dtype = _FakeDtype()

    class _FakeRawHandle:
        """@brief Provide fake RAW handle with conflicting metadata sources."""

        raw_image_visible = _FakeRawImage()

        @property
        def white_level(self) -> int:
            """@brief Return effective-range white level that implies 12-bit."""

            return 4000

    assert dng2hdr2jpg._detect_dng_bits_per_color(_FakeRawHandle()) == 16


def test_compute_auto_ev_value_quantizes_supported_result():
    """
    @brief Validate adaptive EV computation returns supported quantized selector.
    @details Uses deterministic linear preview luminance distribution and
      verifies computed adaptive EV belongs to supported selector set.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-080, REQ-081, REQ-092, REQ-093
    """

    class _FakeRawHandle:
        """@brief Provide fake RAW handle for adaptive EV computation test."""

        @staticmethod
        def postprocess(
            bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
        ):
            assert bright == 1.0
            assert output_bps == 16
            assert use_camera_wb is True
            assert no_auto_bright is True
            assert gamma == (1.0, 1.0)
            assert user_flip == 0
            return [
                [[1000.0, 1000.0, 1000.0]],
                [[8000.0, 8000.0, 8000.0]],
                [[30000.0, 30000.0, 30000.0]],
                [[65000.0, 65000.0, 65000.0]],
            ]

        @property
        def white_level(self) -> int:
            """@brief Return deterministic white level used for bit-depth detection."""

            return 16383

    computed_ev = dng2hdr2jpg._compute_auto_ev_value(_FakeRawHandle())

    expected_ev_values = dng2hdr2jpg._derive_supported_ev_values(14)
    assert computed_ev in expected_ev_values
    assert 0.25 <= computed_ev <= expected_ev_values[-1]
    assert computed_ev * 4 == pytest.approx(round(computed_ev * 4))


def test_derive_scene_key_preserving_median_target_preserves_low_mid_high_key():
    """
    @brief Validate scene-key target derivation preserves low/mid/high classification.
    @details Verifies median target mapping for low-key, mid-key, and high-key input
      medians, ensuring low/high scenes are not forced toward `0.5`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-097, REQ-098
    """

    assert dng2hdr2jpg._derive_scene_key_preserving_median_target(0.2) == pytest.approx(
        0.35
    )
    assert dng2hdr2jpg._derive_scene_key_preserving_median_target(0.5) == pytest.approx(
        0.5
    )
    assert dng2hdr2jpg._derive_scene_key_preserving_median_target(0.8) == pytest.approx(
        0.65
    )


def test_optimize_auto_zero_preserves_scene_key_for_low_key_scene():
    """
    @brief Validate low-key scenes are corrected without forcing neutral key.
    @details Builds auto-zero inputs with low median luminance and verifies solved
      EV-zero uses low-key target (`0.35`) instead of neutral (`0.5`).
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094, REQ-097, REQ-098
    """

    auto_ev_inputs = dng2hdr2jpg.AutoEvInputs(
        p_low=0.01,
        p_median=0.2,
        p_high=0.8,
        target_shadow=dng2hdr2jpg.AUTO_EV_TARGET_SHADOW,
        target_highlight=dng2hdr2jpg.AUTO_EV_TARGET_HIGHLIGHT,
        median_target=dng2hdr2jpg.AUTO_EV_MEDIAN_TARGET,
        ev_zero=0.0,
        ev_values=(0.25, 0.5, 0.75, 1.0, 1.25, 1.5),
    )

    resolved = dng2hdr2jpg._optimize_auto_zero(auto_ev_inputs)

    # log2(0.35/0.2)=0.807... quantized to 0.75 on supported quarter-step grid.
    assert resolved == pytest.approx(0.75)


def test_optimize_auto_zero_preserves_scene_key_for_high_key_scene():
    """
    @brief Validate high-key scenes are corrected without forcing neutral key.
    @details Builds auto-zero inputs with high median luminance and verifies solved
      EV-zero uses high-key target (`0.65`) instead of neutral (`0.5`).
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094, REQ-097, REQ-098
    """

    auto_ev_inputs = dng2hdr2jpg.AutoEvInputs(
        p_low=0.2,
        p_median=0.8,
        p_high=0.99,
        target_shadow=dng2hdr2jpg.AUTO_EV_TARGET_SHADOW,
        target_highlight=dng2hdr2jpg.AUTO_EV_TARGET_HIGHLIGHT,
        median_target=dng2hdr2jpg.AUTO_EV_MEDIAN_TARGET,
        ev_zero=0.0,
        ev_values=(0.25, 0.5, 0.75, 1.0, 1.25, 1.5),
    )

    resolved = dng2hdr2jpg._optimize_auto_zero(auto_ev_inputs)

    # log2(0.65/0.8)=-0.299... quantized to -0.25 on supported quarter-step grid.
    assert resolved == pytest.approx(-0.25)


def test_parse_ev_option_accepts_quarter_step_range():
    """
    @brief Validate `--ev` parser accepts full quarter-step range.
    @details Asserts parser accepts lower bound, mid-range quarter-step, and
      upper bound values aligned to quarter-step granularity.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057
    """

    assert dng2hdr2jpg._parse_ev_option("0.25") == pytest.approx(0.25)
    assert dng2hdr2jpg._parse_ev_option("1.75") == pytest.approx(1.75)
    assert dng2hdr2jpg._parse_ev_option("3.25") == pytest.approx(3.25)


def test_parse_ev_zero_option_accepts_negative_and_positive_quarter_steps():
    """
    @brief Validate `--ev-zero` parser accepts quarter-step signed values.
    @details Asserts parser accepts negative, zero, and positive quarter-step
      values while preserving deterministic rounding behavior.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    assert dng2hdr2jpg._parse_ev_zero_option("-1.25") == pytest.approx(-1.25)
    assert dng2hdr2jpg._parse_ev_zero_option("0") == pytest.approx(0.0)
    assert dng2hdr2jpg._parse_ev_zero_option("2.5") == pytest.approx(2.5)


def test_dng2hdr2jpg_runs_auto_ev_pipeline(monkeypatch, tmp_path):
    """
    @brief Validate adaptive EV pipeline applies default auto-ev percentage scaling.
    @details Mocks adaptive EV solver to deterministic `1.5` and verifies default
      `--auto-ev-pct=50` rescales bracket delta to `0.75` before bracket export
      and luminance merge EV list generation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056, REQ-080, REQ-081, REQ-092, REQ-093, REQ-094
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "luminance_cmd": None,
        "infos": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_extract_normalized_preview_luminance_stats",
        lambda _raw_handle: (0.05, 0.5, 0.95),
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_compute_auto_ev_value_from_stats",
        lambda p_low, p_median, p_high, supported_ev_values, ev_zero=0.0: 1.5,
    )
    monkeypatch.setattr(dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message))

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for adaptive EV run test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for adaptive EV run test."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--auto-ev",
            "--enable-luminance",
        ]
    )

    assert result == 0
    assert observed["brights"] == pytest.approx([2 ** (-0.75), 1.0, 2**0.75])
    assert observed["luminance_cmd"][0] == "luminance-hdr-cli"
    assert observed["luminance_cmd"][2] == "-0.75,0,0.75"
    assert "Detected DNG bits per color: 14" in observed["infos"]
    assert any(
        "Bit-derived EV ceilings: BASE_MAX=3 (formula: (bits_per_color-8)/2), SAFE_ZERO_MAX=2 (formula: BASE_MAX-1), MAX_BRACKET=3 (formula: BASE_MAX-abs(ev_zero))"
        in line
        for line in observed["infos"]
    )


def test_dng2hdr2jpg_rejects_static_ev_above_bit_derived_max(monkeypatch, tmp_path):
    """
    @brief Validate static EV ceiling uses detected DNG bits per color.
    @details Uses fake RAW metadata with `12` bits per color (`MAX=2.0`) and
      asserts `--ev=2.25` is rejected with deterministic non-zero return code.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-092, REQ-093
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "infos": [],
        "errors": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message))
    monkeypatch.setattr(dng2hdr2jpg, "print_error", lambda message: observed["errors"].append(message))

    class _FakeRawHandle12Bit:
        """@brief Provide fake RAW handle with 12-bit white level metadata."""

        def __init__(self, observed_state):
            """@brief Store shared observation map for deterministic extraction."""

            self._observed_state = observed_state

        def __enter__(self):
            """@brief Enter context-manager boundary."""

            return self

        def __exit__(self, exc_type, exc, tb):
            """@brief Exit context-manager boundary and propagate exceptions."""

            del exc_type, exc, tb
            return False

        @property
        def white_level(self) -> int:
            """@brief Return deterministic white level for 12-bit RAW range."""

            return 4095

        def postprocess(
            self, bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
        ):
            """@brief Mirror base fake RAW extraction behavior for pipeline compatibility."""

            self._observed_state["brights"].append(bright)
            self._observed_state["output_bps"].append(output_bps)
            self._observed_state["use_camera_wb"].append(use_camera_wb)
            self._observed_state["no_auto_bright"].append(no_auto_bright)
            self._observed_state["gamma"].append(gamma)
            self._observed_state.setdefault("user_flip", []).append(user_flip)
            return f"rgb-{bright}"

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for bit-derived static EV ceiling test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle12Bit(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for static EV ceiling rejection path."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--enable-enfuse", "--ev=2.25"]
    )

    assert result == 1
    assert "Detected DNG bits per color: 12" in observed["infos"]
    assert any(
        "allowed range for input DNG is 0.25..2 in 0.25 steps" in line
        for line in observed["errors"]
    )


def test_dng2hdr2jpg_rejects_static_ev_above_bit_derived_max_with_ev_zero(
    monkeypatch, tmp_path
):
    """
    @brief Validate static EV ceiling shrinks when `--ev-zero` is set.
    @details Uses fake RAW metadata with 16-bit container (`BASE_MAX=4`) and
      `--ev-zero=-1` (`MAX_BRACKET=3`), then asserts `--ev=3.25` is rejected.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-094, REQ-096
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "infos": [],
        "errors": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message)
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "print_error", lambda message: observed["errors"].append(message)
    )

    class _FakeDtype:
        """@brief Provide deterministic dtype stub with 16-bit itemsize."""

        itemsize = 2

    class _FakeRawImage:
        """@brief Provide fake raw_image_visible metadata container."""

        dtype = _FakeDtype()

    class _FakeRawHandle16Bit:
        """@brief Provide fake RAW handle exposing 16-bit container metadata."""

        raw_image_visible = _FakeRawImage()

        def __init__(self, observed_state):
            """@brief Store shared observation map for deterministic extraction."""

            self._observed_state = observed_state

        def __enter__(self):
            """@brief Enter context-manager boundary."""

            return self

        def __exit__(self, exc_type, exc, tb):
            """@brief Exit context-manager boundary and propagate exceptions."""

            del exc_type, exc, tb
            return False

        @property
        def white_level(self) -> int:
            """@brief Return deterministic white level fallback metadata."""

            return 16383

        def postprocess(
            self, bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
        ):
            """@brief Mirror base fake RAW extraction behavior for compatibility."""

            self._observed_state["brights"].append(bright)
            self._observed_state["output_bps"].append(output_bps)
            self._observed_state["use_camera_wb"].append(use_camera_wb)
            self._observed_state["no_auto_bright"].append(no_auto_bright)
            self._observed_state["gamma"].append(gamma)
            self._observed_state.setdefault("user_flip", []).append(user_flip)
            return f"rgb-{bright}"

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for EV-zero-adjusted max test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle16Bit(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for EV rejection path."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-enfuse",
            "--ev=3.25",
            "--ev-zero=-1",
        ]
    )

    assert result == 1
    assert "Detected DNG bits per color: 16" in observed["infos"]
    assert "Using EV center (ev_zero): -1" in observed["infos"]
    assert any(
        "allowed range for input DNG is 0.25..3 in 0.25 steps" in line
        for line in observed["errors"]
    )


def test_dng2hdr2jpg_rejects_ev_zero_out_of_safe_range(monkeypatch, tmp_path):
    """
    @brief Validate `--ev-zero` range is bounded by safe EV-zero ceiling.
    @details Uses 16-bit RAW metadata (`BASE_MAX=4`, `SAFE_ZERO_MAX=3`) and
      asserts `--ev-zero=-3.25` triggers deterministic runtime validation error.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    observed = {
        "infos": [],
        "errors": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message)
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "print_error", lambda message: observed["errors"].append(message)
    )

    class _FakeDtype:
        """@brief Provide deterministic dtype stub with 16-bit itemsize."""

        itemsize = 2

    class _FakeRawImage:
        """@brief Provide fake raw_image_visible metadata container."""

        dtype = _FakeDtype()

    class _FakeRawHandle16Bit:
        """@brief Provide fake RAW handle exposing 16-bit container metadata."""

        raw_image_visible = _FakeRawImage()

        def __enter__(self):
            """@brief Enter context-manager boundary."""

            return self

        def __exit__(self, exc_type, exc, tb):
            """@brief Exit context-manager boundary and propagate exceptions."""

            del exc_type, exc, tb
            return False

        @property
        def white_level(self) -> int:
            """@brief Return deterministic white level fallback metadata."""

            return 16383

        @staticmethod
        def postprocess(
            bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
        ):
            """@brief Provide deterministic payload for possible extraction path."""

            del bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip
            return "rgb"

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for EV-zero range test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle16Bit()

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for EV-zero range test."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, {"postprocess_ops": []}
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-enfuse",
            "--ev=1",
            "--ev-zero=-3.25",
        ]
    )

    assert result == 1
    assert any("Unsupported --ev-zero value: -3.25" in line for line in observed["errors"])


def test_dng2hdr2jpg_accepts_ev_zero_at_safe_bound(monkeypatch, tmp_path):
    """
    @brief Validate safe EV-zero bound preserves at least `±1EV` bracket.
    @details Uses 12-bit RAW metadata (`BASE_MAX=2`, `SAFE_ZERO_MAX=1`) with
      `--ev-zero=1` and verifies successful static pipeline execution with
      deterministic `MAX_BRACKET=1`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-096
    """

    observed = {
        "infos": [],
        "errors": [],
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "writes": [],
        "enfuse_cmd": None,
        "tmp_dir": None,
        "copy_calls": [],
        "output_exists_after_copy": None,
        "output_exists_before_copy": None,
        "tiff_reads": [],
        "raw_handles": [],
        "output_mode_before_convert": [],
        "output_jpg_compression": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message)
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "print_error", lambda message: observed["errors"].append(message)
    )

    class _FakeRawHandle12Bit:
        """@brief Provide fake RAW handle with 12-bit white level metadata."""

        @property
        def white_level(self) -> int:
            """@brief Return deterministic white level for 12-bit RAW range."""

            return 4095

        def __enter__(self):
            """@brief Enter context-manager boundary."""

            return self

        def __exit__(self, exc_type, exc, tb):
            """@brief Exit context-manager boundary and propagate exceptions."""

            del exc_type, exc, tb
            return False

        def __init__(self, observed_state):
            """@brief Store shared observation map for deterministic extraction."""

            self._observed_state = observed_state

        def postprocess(
            self,
            bright,
            output_bps,
            use_camera_wb,
            no_auto_bright,
            gamma,
            user_flip=None,
        ):
            """@brief Capture extraction arguments and return deterministic payload."""

            self._observed_state["brights"].append(bright)
            self._observed_state["output_bps"].append(output_bps)
            self._observed_state["use_camera_wb"].append(use_camera_wb)
            self._observed_state["no_auto_bright"].append(no_auto_bright)
            self._observed_state["gamma"].append(gamma)
            self._observed_state.setdefault("user_flip", []).append(user_flip)
            return f"rgb-{bright}"

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for low `MAX_BRACKET` test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle12Bit(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for low `MAX_BRACKET` test."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, {"postprocess_ops": []}
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_run_enfuse",
        lambda bracket_paths, merged_tiff: Path(merged_tiff).write_text(
            "merged", encoding="utf-8"
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_sync_output_file_timestamps_from_exif",
        lambda output_jpg, exif_timestamp: None,
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "tempfile",
        type(
            "_FakeTempfile",
            (),
            {
                "TemporaryDirectory": lambda *args, **kwargs: _TrackingTemporaryDirectory(
                    observed, *args, **kwargs
                )
            },
        ),
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-enfuse",
            "--ev=1",
            "--ev-zero=1",
        ]
    )

    assert result == 0
    assert "Using EV center (ev_zero): 1" in observed["infos"]
    assert any(
        "Using EV bracket delta: 1 (static)" in line for line in observed["infos"]
    )


def test_dng2hdr2jpg_uses_static_ev_and_runs_hdr_pipeline(monkeypatch, tmp_path):
    """
    @brief Validate static EV behavior and complete HDR pipeline invocation.
    @details Mocks rawpy/imageio/subprocess boundaries and asserts multiplier
      sequence, enfuse command shape, JPG output creation, and temp cleanup.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-079, REQ-092
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
        "infos": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message))

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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
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

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=2", "--enable-enfuse"]
    )

    assert result == 0
    assert observed["brights"] == pytest.approx([0.25, 1.0, 4.0])
    assert observed["output_bps"] == [16, 16, 16]
    assert observed["use_camera_wb"] == [True, True, True]
    assert observed["no_auto_bright"] == [True, True, True]
    assert observed["gamma"] == [(2.222, 4.5), (2.222, 4.5), (2.222, 4.5)]
    assert observed["user_flip"] == [0, 0, 0]
    assert observed["enfuse_cmd"][0] == "enfuse"
    assert len(observed["enfuse_cmd"]) == 6
    assert "postprocess_ops" not in observed
    assert "Detected DNG bits per color: 14" in observed["infos"]
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_runs_luminance_backend_with_default_operator(
    monkeypatch, tmp_path
):
    """
    @brief Validate luminance-hdr-cli backend execution with default parameters.
    @details Enables luminance mode and verifies command argv shape uses
      `luminance-hdr-cli -e <ev-list> --hdrModel debevec --hdrWeight flat`
      `--hdrResponseCurve srgb --tmo mantiuk08 --ldrTiff 16b -o <merged_hdr.tif>`
      plus three ordered bracket TIFF inputs.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-060, REQ-061, REQ-062, REQ-068, REQ-091
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
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

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--enable-luminance", "--ev=1"]
    )

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
        "mantiuk08",
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
    assert ("contrast", 1.2) in observed["postprocess_ops"]
    assert output_jpg.exists()
    assert observed["tmp_dir"] is not None
    assert not observed["tmp_dir"].exists()


def test_dng2hdr2jpg_luminance_sidecar_pp3_isolated_from_caller_cwd(
    monkeypatch, tmp_path
):
    """
    @brief Validate luminance execution does not leave `.pp3` sidecars in caller CWD.
    @details Simulates `luminance-hdr-cli` sidecar generation in current working
      directory and verifies the command pipeline isolates backend execution so
      sidecar artifacts are removed with temporary intermediates.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059, REQ-062
    """

    observed = {"luminance_cmd": None}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for sidecar cleanup test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager for the provided path."""

            return _FakeRawHandle(
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
            )

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for deterministic TIFF I/O."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic bracket TIFF placeholder."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for shared JPG encode stage."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    sidecar_name = "luminance-hdr-cli-sidecar.pp3"
    sidecar_path = tmp_path / sidecar_name

    def _fake_subprocess_run(command, check):
        """@brief Simulate luminance backend writing `.pp3` in process CWD."""

        assert check is True
        if command and command[0] == "luminance-hdr-cli":
            observed["luminance_cmd"] = command
            Path(sidecar_name).write_text("pp3", encoding="utf-8")
            output_index = command.index("-o") + 1
            Path(command[output_index]).write_text("hdr", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        if command and command[0] == "magick":
            Path(command[-1]).write_text("jpg", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"Unexpected command: {command!r}")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.chdir(tmp_path)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--enable-luminance", "--ev=1"]
    )

    assert result == 0
    assert observed["luminance_cmd"] is not None
    assert not sidecar_path.exists()


def test_dng2hdr2jpg_uses_ev_zero_to_center_static_bracketing(monkeypatch, tmp_path):
    """
    @brief Validate `--ev-zero` recenters static bracketing triplet.
    @details Runs static mode with `--ev=2` and `--ev-zero=-1`, verifies
      extracted brightness multipliers match center `-1` and luminance EV list
      is centered at `0` with the same delta (`-2,0,2`),
      and verifies shared JPG-encode stage receives `ev_zero=-1`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-062, REQ-094, REQ-095
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "luminance_cmd": None,
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module surface for EV-zero centering test."""

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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_encode_jpg",
        lambda **kwargs: (
            observed.__setitem__("encode_ev_zero", kwargs["ev_zero"]),
            Path(kwargs["output_jpg"]).write_text("jpg", encoding="utf-8"),
        )[-1],
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-luminance",
            "--ev=2",
            "--ev-zero=-1",
        ]
    )

    assert result == 0
    assert observed["brights"] == pytest.approx([2**-3, 2**-1, 2**1])
    assert observed["luminance_cmd"][2] == "-2,0,2"
    assert observed["encode_ev_zero"] == pytest.approx(-1.0)


def test_dng2hdr2jpg_auto_zero_resolves_center_and_recenters_luminance_merge(
    monkeypatch, tmp_path
):
    """
    @brief Validate `--auto-zero` resolves EV center and keeps merge EV list centered on zero.
    @details Runs static mode with `--ev=2` and `--auto-zero`, stubs auto-zero
      optimization to `-1`, verifies default `--auto-zero-pct=50` rescales center
      to `-0.5`, and verifies luminance merge EV list remains zero-centered.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094, REQ-095, REQ-097
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "luminance_cmd": None,
        "infos": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")
    monkeypatch.setattr(
        dng2hdr2jpg, "print_info", lambda message: observed["infos"].append(message)
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_extract_normalized_preview_luminance_stats",
        lambda _raw_handle: (0.01, 1.0, 0.99),
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_optimize_auto_zero",
        lambda _auto_ev_inputs: -1.0,
    )

    class _FakeRawPyModule:
        """@brief Provide fake `rawpy` module for auto-zero center resolution test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for auto-zero center resolution test."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_encode_jpg",
        lambda **kwargs: (
            observed.__setitem__("encode_ev_zero", kwargs["ev_zero"]),
            Path(kwargs["output_jpg"]).write_text("jpg", encoding="utf-8"),
        )[-1],
    )

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--enable-luminance",
            "--ev=2",
            "--auto-zero",
        ]
    )

    assert result == 0
    assert observed["brights"] == pytest.approx([2 ** -2.5, 2**-0.5, 2**1.5])
    assert observed["luminance_cmd"][2] == "-2,0,2"
    assert observed["encode_ev_zero"] == pytest.approx(-0.5)
    assert "Using EV center mode: auto-zero" in observed["infos"]


def test_write_bracket_images_disables_raw_orientation_auto_flip(tmp_path):
    """
    @brief Reproduce orientation defect in RAW bracket extraction path.
    @details Calls `_write_bracket_images` with a fake RAW handle that records
      `user_flip` values from `raw.postprocess`; expected behavior requires
      explicit `user_flip=0` to disable implicit orientation mutation.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-057, REQ-077
    """

    observed = {"user_flip": [], "writes": []}

    class _FakeRawHandle:
        """@brief Provide fake RAW handle that records postprocess options."""

        @staticmethod
        def postprocess(
            bright, output_bps, use_camera_wb, no_auto_bright, gamma, user_flip=None
        ):
            observed["user_flip"].append(user_flip)
            assert output_bps == 16
            assert use_camera_wb is True
            assert no_auto_bright is True
            assert gamma == (2.222, 4.5)
            return f"rgb-{bright}"

    class _FakeImageIoModule:
        """@brief Provide fake imageio module that records TIFF writes."""

        @staticmethod
        def imwrite(path, _data):
            observed["writes"].append(Path(path).name)
            Path(path).write_text("payload", encoding="utf-8")

    bracket_paths = dng2hdr2jpg._write_bracket_images(
        raw_handle=_FakeRawHandle,
        imageio_module=_FakeImageIoModule,
        multipliers=(0.25, 1.0, 4.0),
        gamma_value=(2.222, 4.5),
        temp_dir=tmp_path,
    )

    assert [path.name for path in bracket_paths] == [
        "ev_minus.tif",
        "ev_zero.tif",
        "ev_plus.tif",
    ]
    assert observed["writes"] == ["ev_minus.tif", "ev_zero.tif", "ev_plus.tif"]
    assert observed["user_flip"] == [0, 0, 0]


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
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--ev=2",
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
    assert [Path(value).name for value in command[21:]] == [
        "ev_minus.tif",
        "ev_zero.tif",
        "ev_plus.tif",
    ]


def test_dng2hdr2jpg_luminance_non_tuned_defaults_remain_neutral(
    monkeypatch, tmp_path
):
    """
    @brief Validate neutral postprocess defaults for non-tuned luminance TMOs.
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
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--ev=2",
            "--enable-luminance",
            "--luminance-tmo=drago",
        ]
    )

    assert result == 0
    assert "--tmo" in observed["command"]
    tmo_index = observed["command"].index("--tmo")
    assert observed["command"][tmo_index + 1] == "drago"
    assert "postprocess_ops" not in observed


def test_dng2hdr2jpg_luminance_reinhard02_defaults_remain_tuned(
    monkeypatch, tmp_path
):
    """
    @brief Validate reinhard02 tuned postprocess defaults remain unchanged.
    @details Selects luminance backend with explicit `--luminance-tmo=reinhard02`
      and asserts tuned defaults for brightness/contrast/saturation are applied.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-069
    """

    observed = {"command": []}
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for reinhard02 tuned defaults test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW handle."""

            return _FakeRawHandle(
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
            )

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for reinhard02 tuned defaults test."""

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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--ev=2",
            "--enable-luminance",
            "--luminance-tmo=reinhard02",
        ]
    )

    assert result == 0
    assert "--tmo" in observed["command"]
    tmo_index = observed["command"].index("--tmo")
    assert observed["command"][tmo_index + 1] == "reinhard02"
    assert ("brightness", 1.25) in observed["postprocess_ops"]
    assert ("contrast", 0.85) in observed["postprocess_ops"]
    assert ("saturation", 0.55) in observed["postprocess_ops"]


def test_dng2hdr2jpg_returns_error_and_cleans_temp_on_enfuse_failure(
    monkeypatch, tmp_path
):
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
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
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

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=1.5", "--enable-enfuse"]
    )

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

    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--ev=1", "--enable-enfuse", "--gamma=1"]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--gamma=a,b",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--gamma=0,1",
            ]
        )
        == 1
    )


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

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--post-gamma=0",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--brightness=foo",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--contrast=-1",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--saturation=0",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--jpg-compression=200",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--jpg-compression=bad",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--auto-adjust=1",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_missing_and_unknown_auto_adjust_mode(tmp_path):
    """
    @brief Validate auto-adjust mode parser rejects missing and unknown values.
    @details Exercises `--auto-adjust` token without value and with unsupported mode
      selector and asserts deterministic parse failures.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-073, REQ-075, REQ-085
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--auto-adjust",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--auto-adjust",
                "Unknown",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_auto_adjust_knobs_without_auto_adjust(tmp_path):
    """
    @brief Validate `--aa-*` knobs are rejected when `--auto-adjust` is omitted.
    @details Exercises both assignment and split knob forms without
      `--auto-adjust` and asserts deterministic parser failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-082, REQ-085
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--aa-blur-sigma=1.1",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--aa-sigmoid-midpoint",
                "0.4",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_auto_brightness_knobs_without_auto_brightness(tmp_path):
    """
    @brief Validate `--ab-*` knobs are rejected when `--auto-brightness` is omitted.
    @details Exercises assignment and split knob forms without `--auto-brightness`
      and asserts deterministic parser failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-089
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--ab-target-grey=0.21",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--ab-target-grey",
                "0.21",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_invalid_auto_brightness_knob_values(tmp_path):
    """
    @brief Validate auto-brightness knob validation constraints.
    @details Verifies positive-only, bounded-range, and formatting rules for
      `--ab-target-grey` option when auto-brightness mode is enabled.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-089
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"
    base_args = [
        str(input_dng),
        str(output_jpg),
        "--ev=1",
        "--enable-enfuse",
        "--auto-brightness",
    ]

    assert dng2hdr2jpg.run(base_args + ["--ab-target-grey=0"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--ab-target-grey=1"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--ab-target-grey=bad"]) == 1


def test_dng2hdr2jpg_parses_auto_brightness_knob_assignment_and_split_forms():
    """
    @brief Validate parser handles `--ab-target-grey` assignment and split forms.
    @details Parses mixed-form auto-brightness knobs and verifies canonical
      propagation into `PostprocessOptions.auto_brightness_options`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-088, REQ-089
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
            "--auto-brightness=true",
            "--ab-target-grey=0.23",
        ]
    )
    assert parsed is not None
    postprocess_options = parsed[5]
    assert postprocess_options.auto_brightness_enabled is True
    auto_brightness_options = postprocess_options.auto_brightness_options
    assert auto_brightness_options.target_grey == 0.23


def test_dng2hdr2jpg_auto_brightness_knobs_default_values_are_stable():
    """
    @brief Validate auto-brightness defaults remain stable.
    @details Parses options with enabled auto-brightness and no explicit `--ab-*`
      overrides, then asserts all default values match constants.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-088
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
            "--auto-brightness",
        ]
    )
    assert parsed is not None
    options = parsed[5].auto_brightness_options
    assert options.target_grey == dng2hdr2jpg.DEFAULT_AB_TARGET_GREY


def test_dng2hdr2jpg_auto_brightness_accepts_split_boolean_value():
    """
    @brief Validate `--auto-brightness` accepts split boolean value form.
    @details Parses split form `--auto-brightness yes` and verifies enabled state.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
            "--auto-brightness",
            "yes",
        ]
    )
    assert parsed is not None
    assert parsed[5].auto_brightness_enabled is True


def test_dng2hdr2jpg_parse_run_options_defaults_ev_zero_to_zero():
    """
    @brief Validate parser defaults EV center and percentage scaling knobs.
    @details Parses minimal valid static selector argv and verifies deterministic
      defaults for `ev_zero`, `auto_zero_enabled`, `auto_zero_pct`, and `auto_ev_pct`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
        ]
    )
    assert parsed is not None
    assert parsed[8] == pytest.approx(0.0)
    assert parsed[9] is False
    assert parsed[10] == pytest.approx(50.0)
    assert parsed[11] == pytest.approx(50.0)


def test_dng2hdr2jpg_parse_run_options_accepts_auto_percentage_overrides():
    """
    @brief Validate parser accepts auto percentage scaling options.
    @details Parses explicit `--auto-zero-pct` and `--auto-ev-pct` values and
      verifies returned tuple stores deterministic numeric percentages.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--auto-ev",
            "--auto-zero",
            "--auto-zero-pct=75",
            "--auto-ev-pct",
            "25",
            "--enable-enfuse",
        ]
    )
    assert parsed is not None
    assert parsed[10] == pytest.approx(75.0)
    assert parsed[11] == pytest.approx(25.0)


def test_dng2hdr2jpg_parse_run_options_rejects_invalid_auto_percentage_overrides():
    """
    @brief Validate parser rejects invalid auto percentage scaling options.
    @details Verifies malformed and out-of-range percentage values fail parsing
      deterministically for both auto-zero and auto-ev percentage options.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    parsed_invalid_text = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--auto-zero-pct=bad",
            "--enable-enfuse",
        ]
    )
    assert parsed_invalid_text is None

    parsed_invalid_range = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--auto-ev",
            "--auto-ev-pct=101",
            "--enable-enfuse",
        ]
    )
    assert parsed_invalid_range is None


def test_dng2hdr2jpg_parse_run_options_accepts_ev_zero_split_and_assignment_forms():
    """
    @brief Validate parser accepts `--ev-zero` split and assignment forms.
    @details Parses both forms and verifies tuple field stores requested center.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    parsed_split = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--ev-zero",
            "-0.75",
            "--enable-enfuse",
        ]
    )
    assert parsed_split is not None
    assert parsed_split[8] == pytest.approx(-0.75)
    assert parsed_split[9] is False

    parsed_assignment = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--auto-ev",
            "--ev-zero=1.25",
            "--enable-enfuse",
        ]
    )
    assert parsed_assignment is not None
    assert parsed_assignment[8] == pytest.approx(1.25)
    assert parsed_assignment[9] is False


def test_dng2hdr2jpg_parse_run_options_accepts_auto_zero_split_and_assignment_forms():
    """
    @brief Validate parser accepts `--auto-zero` split and assignment forms.
    @details Parses both forms and verifies tuple field stores deterministic
      `auto_zero_enabled=True`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094, REQ-097
    """

    parsed_split = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--auto-zero",
            "--enable-enfuse",
        ]
    )
    assert parsed_split is not None
    assert parsed_split[9] is True

    parsed_assignment = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--auto-ev",
            "--auto-zero=true",
            "--enable-enfuse",
        ]
    )
    assert parsed_assignment is not None
    assert parsed_assignment[9] is True


def test_dng2hdr2jpg_rejects_mixed_ev_zero_and_auto_zero(tmp_path):
    """
    @brief Validate parser rejects simultaneous manual and auto EV-zero selectors.
    @details Provides both `--ev-zero` and `--auto-zero` with valid remaining
      arguments and expects deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--ev-zero=-0.5",
                "--auto-zero",
                "--enable-enfuse",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_invalid_ev_zero_value(tmp_path):
    """
    @brief Validate `--ev-zero` parser rejects unsupported values.
    @details Provides malformed and non-quarter-step `--ev-zero` values with
      valid selectors and asserts deterministic parse failure.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-094
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--ev-zero=bad",
                "--enable-enfuse",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--ev-zero=0.1",
                "--enable-enfuse",
            ]
        )
        == 1
    )


def test_dng2hdr2jpg_rejects_invalid_auto_adjust_knob_values(tmp_path):
    """
    @brief Validate shared auto-adjust knob validation constraints.
    @details Verifies positive-only, bounded-range, and `low < high` validation
      rules for `--aa-*` options when auto-adjust mode is enabled.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-082, REQ-084
    """

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "result.jpg"
    base_args = [
        str(input_dng),
        str(output_jpg),
        "--ev=1",
        "--enable-enfuse",
        "--auto-adjust",
        "ImageMagick",
    ]

    assert dng2hdr2jpg.run(base_args + ["--aa-blur-sigma=0"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-sigmoid-contrast", "-1"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-saturation-gamma=0"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-highpass-blur-sigma=0"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-blur-threshold-pct=101"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-level-low-pct=-1"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-level-high-pct=101"]) == 1
    assert dng2hdr2jpg.run(base_args + ["--aa-sigmoid-midpoint=1.1"]) == 1
    assert (
        dng2hdr2jpg.run(
            base_args + ["--aa-level-low-pct=80", "--aa-level-high-pct=20"]
        )
        == 1
    )


def test_dng2hdr2jpg_parses_auto_adjust_knob_assignment_and_split_forms():
    """
    @brief Validate parser handles `--aa-*` assignment and split forms.
    @details Parses mixed-form knob options and verifies canonical option
      propagation into `PostprocessOptions.auto_adjust_options`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-082, REQ-083, REQ-084
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
            "--auto-adjust",
            "OpenCV",
            "--aa-blur-sigma=1.5",
            "--aa-blur-threshold-pct",
            "12.5",
            "--aa-level-low-pct=2",
            "--aa-level-high-pct",
            "98",
            "--aa-sigmoid-contrast",
            "4",
            "--aa-sigmoid-midpoint=0.45",
            "--aa-saturation-gamma",
            "0.9",
            "--aa-highpass-blur-sigma=3.3",
        ]
    )
    assert parsed is not None
    postprocess_options = parsed[5]
    auto_adjust_options = postprocess_options.auto_adjust_options
    assert auto_adjust_options.blur_sigma == 1.5
    assert auto_adjust_options.blur_threshold_pct == 12.5
    assert auto_adjust_options.level_low_pct == 2.0
    assert auto_adjust_options.level_high_pct == 98.0
    assert auto_adjust_options.sigmoid_contrast == 4.0
    assert auto_adjust_options.sigmoid_midpoint == 0.45
    assert auto_adjust_options.saturation_gamma == 0.9
    assert auto_adjust_options.highpass_blur_sigma == 3.3


def test_dng2hdr2jpg_auto_adjust_knobs_default_values_are_stable():
    """
    @brief Validate shared auto-adjust knob defaults remain backward compatible.
    @details Parses options with enabled auto-adjust and no explicit `--aa-*`
      overrides, then asserts all shared knob defaults match legacy constants.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-083
    """

    parsed = dng2hdr2jpg._parse_run_options(
        [
            "input.dng",
            "output.jpg",
            "--ev=1",
            "--enable-enfuse",
            "--auto-adjust",
            "ImageMagick",
        ]
    )
    assert parsed is not None
    auto_adjust_options = parsed[5].auto_adjust_options
    assert auto_adjust_options.blur_sigma == dng2hdr2jpg.DEFAULT_AA_BLUR_SIGMA
    assert (
        auto_adjust_options.blur_threshold_pct
        == dng2hdr2jpg.DEFAULT_AA_BLUR_THRESHOLD_PCT
    )
    assert auto_adjust_options.level_low_pct == dng2hdr2jpg.DEFAULT_AA_LEVEL_LOW_PCT
    assert auto_adjust_options.level_high_pct == dng2hdr2jpg.DEFAULT_AA_LEVEL_HIGH_PCT
    assert (
        auto_adjust_options.sigmoid_contrast
        == dng2hdr2jpg.DEFAULT_AA_SIGMOID_CONTRAST
    )
    assert (
        auto_adjust_options.sigmoid_midpoint
        == dng2hdr2jpg.DEFAULT_AA_SIGMOID_MIDPOINT
    )
    assert (
        auto_adjust_options.saturation_gamma
        == dng2hdr2jpg.DEFAULT_AA_SATURATION_GAMMA
    )
    assert (
        auto_adjust_options.highpass_blur_sigma
        == dng2hdr2jpg.DEFAULT_AA_HIGHPASS_BLUR_SIGMA
    )


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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
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

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=1", "--enable-enfuse", "--gamma=1,1"]
    )

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

            return _FakeRawHandle(
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
            )

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

    def _fake_write_brackets(
        raw_handle, imageio_module, multipliers, gamma_value, temp_dir
    ):
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
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: (
            "/usr/bin/luminance-hdr-cli" if cmd == "luminance-hdr-cli" else None
        ),
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg, "_write_bracket_images", _fake_write_brackets)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=2", "--enable-luminance"]
    )

    assert result == 0
    command = observed["command"]
    assert command
    assert [Path(value).name for value in command[-3:]] == [
        "ev_minus.tif",
        "ev_zero.tif",
        "ev_plus.tif",
    ]


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

    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=1", "--enable-enfuse"])
        == 1
    )


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

    assert (
        dng2hdr2jpg.run(
            [str(input_dng), str(output_jpg), "--ev=1", "--enable-luminance"]
        )
        == 1
    )


def test_dng2hdr2jpg_auto_adjust_uses_convert_when_magick_is_missing(
    monkeypatch, tmp_path
):
    """
    @brief Reproduce auto-adjust dependency bug when only `convert` binary is available.
    @details Configures dependency lookup so `magick` is missing but `convert`
      exists; expected behavior is successful auto-adjust execution path for backward-
      compatible ImageMagick CLI naming.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-059, REQ-073
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
        """@brief Provide fake `rawpy` module for auto-adjust dependency fallback test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            """@brief Return fake RAW context manager."""

            return _FakeRawHandle(observed)

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for auto-adjust dependency fallback test."""

        @staticmethod
        def imwrite(path, _data):
            """@brief Materialize deterministic placeholder files."""

            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            """@brief Return merged/auto-adjust payload compatible with encode path."""

            name = Path(path).name
            if name in {"merged_hdr.tif", "auto_adjust_output.tif"}:
                return _FakeImage16()
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Emulate successful backend and auto-adjust subprocess executions."""

        assert check is True
        if command and command[0] == "enfuse":
            output_flag = next(
                token for token in command if token.startswith("--output=")
            )
            Path(output_flag.split("=", 1)[1]).write_text("merged", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        if command and command[0] == "convert":
            Path(command[-1]).write_text("auto-adjust", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: _build_fake_dependencies(
            _FakeRawPyModule, _FakeImageIoModule, observed
        ),
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

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--ev=1",
            "--enable-enfuse",
            "--auto-adjust",
            "ImageMagick",
        ]
    )

    assert result == 0
    assert output_jpg.exists()


def test_dng2hdr2jpg_fails_when_auto_adjust_opencv_dependencies_are_missing(
    monkeypatch, tmp_path
):
    """
    @brief Validate OpenCV auto-adjust mode fails when Python dependencies are missing.
    @details Enables auto-adjust with `OpenCV`, forces dependency resolver failure, and
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
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "_resolve_auto_adjust_opencv_dependencies", lambda: None
    )

    result = dng2hdr2jpg.run(
        [
            str(input_dng),
            str(output_jpg),
            "--ev=1",
            "--enable-enfuse",
            "--auto-adjust",
            "OpenCV",
        ]
    )

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

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--luminance-tmo=fattal",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--luminance-hdr-model=robertson",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-enfuse",
                "--tmoR05Brightness=0",
            ]
        )
        == 1
    )


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

    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-luminance",
                "--luminance-tmo=",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-luminance",
                "--luminance-hdr-model",
                "",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-luminance",
                "--tmoR05Brightness",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-luminance",
                "--tmoR05Chroma=",
            ]
        )
        == 1
    )
    assert (
        dng2hdr2jpg.run(
            [
                str(input_dng),
                str(output_jpg),
                "--ev=1",
                "--enable-luminance",
                "--tmoR05Lightness",
                "--invalid",
            ]
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

    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=1", "--enable-enfuse"])
        == 1
    )


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

    assert (
        dng2hdr2jpg.run([str(input_dng), str(output_jpg), "--ev=1", "--enable-enfuse"])
        == 1
    )


def test_dng2hdr2jpg_runtime_dependencies_are_declared_in_pyproject():
    """
    @brief Validate runtime dependency declaration for DNG processing modules.
    @details Parses `pyproject.toml` and asserts that `rawpy`, `imageio`,
      `pillow`, `piexif`, `numpy`, and `opencv-python`
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
    assert any(dep.startswith("piexif") for dep in dependencies)
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
    @satisfies TST-011, REQ-066, REQ-074, REQ-077, REQ-078
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
        "refresh_calls": [],
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
                274: 6,
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

        def save(
            self,
            path,
            format,
            quality=None,
            optimize=None,
            exif=None,
            compress_level=None,
        ):
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

    fake_piexif_module = object()

    def _fake_refresh_output_jpg_exif_thumbnail_after_save(
        pil_image_module,
        piexif_module,
        output_jpg,
        source_exif_payload,
        source_orientation,
    ):
        """@brief Capture EXIF thumbnail refresh call arguments."""

        observed["refresh_calls"].append(
            {
                "pil_image_module": pil_image_module,
                "piexif_module": piexif_module,
                "output_jpg": Path(output_jpg),
                "source_exif_payload": source_exif_payload,
                "source_orientation": source_orientation,
            }
        )

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: (
            _FakeRawPyModule,
            _FakeImageIoModule,
            _FakePilImageModule,
            _FakePilEnhanceModule,
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "_load_piexif_dependency", lambda: fake_piexif_module
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_refresh_output_jpg_exif_thumbnail_after_save",
        _fake_refresh_output_jpg_exif_thumbnail_after_save,
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg.os, "utime", _fake_utime)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=2", "--enable-enfuse"]
    )

    assert result == 0
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["exif"] == b"fake-exif-payload"
    assert len(observed["refresh_calls"]) == 1
    assert observed["refresh_calls"][0]["piexif_module"] is fake_piexif_module
    assert observed["refresh_calls"][0]["output_jpg"] == output_jpg
    assert observed["refresh_calls"][0]["source_exif_payload"] == b"fake-exif-payload"
    assert observed["refresh_calls"][0]["source_orientation"] == 6
    assert len(observed["utime_calls"]) == 1
    utime_path, utime_values = observed["utime_calls"][0]
    assert utime_path == output_jpg
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2024:07:08 09:10:11"
    )
    assert utime_values == (expected_timestamp, expected_timestamp)


def test_dng2hdr2jpg_sets_jpg_timestamps_when_exif_datetime_is_sequence(
    monkeypatch, tmp_path
):
    """
    @brief Validate timestamp synchronization when EXIF datetime is sequence-like.
    @details Runs enfuse flow with `DateTimeOriginal` represented as one-item
      tuple containing null-terminated bytes and verifies output JPG filesystem
      timestamps are still synchronized from EXIF datetime.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-074, REQ-077
    """

    observed = {
        "utime_calls": [],
        "jpg_save": None,
        "refresh_calls": [],
    }
    monkeypatch.setattr(dng2hdr2jpg, "get_runtime_os", lambda: "linux")

    class _FakeRawPyModule:
        """@brief Provide fake rawpy module for sequence-like datetime test."""

        LibRawError = RuntimeError

        @staticmethod
        def imread(_path):
            return _FakeRawHandle(
                {
                    "brights": [],
                    "output_bps": [],
                    "use_camera_wb": [],
                    "no_auto_bright": [],
                    "gamma": [],
                }
            )

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for minimal pipeline execution."""

        @staticmethod
        def imwrite(path, _data):
            Path(path).write_text("payload", encoding="utf-8")

        @staticmethod
        def imread(path):
            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    class _FakeExif:
        """@brief Provide fake EXIF payload with sequence-style datetime value."""

        @staticmethod
        def get(key):
            if key == 274:
                return 6
            if key == 36867:
                return (b"2024:07:08 09:10:11\x00",)
            return None

        @staticmethod
        def tobytes():
            return b"fake-exif-payload"

    class _FakeDngImage:
        """@brief Provide fake source DNG image exposing `getexif`."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        @staticmethod
        def getexif():
            return _FakeExif()

    class _FakePilImage:
        """@brief Provide fake PIL image object for JPEG save assertions."""

        mode = "RGB"

        @staticmethod
        def getbands():
            return ("R", "G", "B")

        def point(self, _lut):
            return self

        def convert(self, _target_mode):
            return self

        def save(
            self,
            path,
            format,
            quality=None,
            optimize=None,
            exif=None,
            compress_level=None,
        ):
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

    fake_piexif_module = object()

    def _fake_refresh_output_jpg_exif_thumbnail_after_save(
        pil_image_module,
        piexif_module,
        output_jpg,
        source_exif_payload,
        source_orientation,
    ):
        observed["refresh_calls"].append(
            {
                "pil_image_module": pil_image_module,
                "piexif_module": piexif_module,
                "output_jpg": Path(output_jpg),
                "source_exif_payload": source_exif_payload,
                "source_orientation": source_orientation,
            }
        )

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: (
            _FakeRawPyModule,
            _FakeImageIoModule,
            _FakePilImageModule,
            _FakePilEnhanceModule,
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "_load_piexif_dependency", lambda: fake_piexif_module
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_refresh_output_jpg_exif_thumbnail_after_save",
        _fake_refresh_output_jpg_exif_thumbnail_after_save,
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg.os, "utime", _fake_utime)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=2", "--enable-enfuse"]
    )

    assert result == 0
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["exif"] == b"fake-exif-payload"
    assert len(observed["refresh_calls"]) == 1
    assert observed["refresh_calls"][0]["piexif_module"] is fake_piexif_module
    assert observed["refresh_calls"][0]["output_jpg"] == output_jpg
    assert observed["refresh_calls"][0]["source_exif_payload"] == b"fake-exif-payload"
    assert observed["refresh_calls"][0]["source_orientation"] == 6
    assert len(observed["utime_calls"]) == 1
    utime_path, utime_values = observed["utime_calls"][0]
    assert utime_path == output_jpg
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2024:07:08 09:10:11"
    )
    assert utime_values == (expected_timestamp, expected_timestamp)


def test_extract_dng_exif_payload_preserves_source_orientation_tag():
    """
    @brief Validate DNG EXIF extraction preserves source orientation metadata.
    @details Builds a fake DNG EXIF container with camera orientation `6` and
      verifies extractor preserves orientation value in serialized payload and
      emits orientation scalar for downstream pipeline invariants.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-077
    """

    class _FakeExif:
        """@brief Provide mutable EXIF map and deterministic serialized payload."""

        def __init__(self):
            self._values = {274: 6, 36867: "2024:07:08 09:10:11"}

        def get(self, key):
            """@brief Return EXIF value for requested numeric tag."""

            return self._values.get(key)

        def tobytes(self):
            """@brief Encode current orientation value into payload marker."""

            orientation = self._values.get(274)
            return f"orientation={orientation}".encode("utf-8")

    class _FakeSourceImage:
        """@brief Provide fake source image exposing `getexif` context surface."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        @staticmethod
        def getexif():
            return _FakeExif()

    class _FakePilImageModule:
        """@brief Provide fake PIL module exposing `open` callable."""

        @staticmethod
        def open(_path):
            return _FakeSourceImage()

    exif_payload, exif_timestamp, source_orientation = (
        dng2hdr2jpg._extract_dng_exif_payload_and_timestamp(
            pil_image_module=_FakePilImageModule,
            input_dng=Path("scene.dng"),
        )
    )

    assert exif_payload == b"orientation=6"
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2024:07:08 09:10:11"
    )
    assert exif_timestamp == expected_timestamp
    assert source_orientation == 6


def test_extract_dng_exif_payload_suppresses_tiff_tag_33723_warning():
    """
    @brief Reproduce noisy PIL metadata warning during EXIF extraction.
    @details Emits explicit `PIL.TiffImagePlugin` warning for TIFF tag `33723`
      from fake `getexif` path and verifies extractor suppresses this known
      non-actionable warning while preserving EXIF payload and timestamp parse.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-074
    """

    class _FakeExif:
        """@brief Provide deterministic EXIF values for warning-suppression test."""

        @staticmethod
        def get(key):
            if key == 274:
                return 1
            if key == 36867:
                return "2024:07:08 09:10:11"
            return None

        @staticmethod
        def tobytes():
            return b"exif-warning-test"

    class _FakeSourceImage:
        """@brief Provide fake source image surface for EXIF extraction test."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        @staticmethod
        def getexif():
            warnings.warn_explicit(
                "Metadata Warning, tag 33723 had too many entries: 15, expected 1",
                UserWarning,
                filename="/tmp/PIL/TiffImagePlugin.py",
                lineno=759,
                module="PIL.TiffImagePlugin",
            )
            return _FakeExif()

    class _FakePilImageModule:
        """@brief Provide fake PIL module exposing deterministic `open`."""

        @staticmethod
        def open(_path):
            return _FakeSourceImage()

    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")
        exif_payload, exif_timestamp, source_orientation = (
            dng2hdr2jpg._extract_dng_exif_payload_and_timestamp(
                pil_image_module=_FakePilImageModule,
                input_dng=Path("scene.dng"),
            )
        )

    assert exif_payload == b"exif-warning-test"
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2024:07:08 09:10:11"
    )
    assert exif_timestamp == expected_timestamp
    assert source_orientation == 1
    assert not any(
        "tag 33723 had too many entries" in str(w.message) for w in captured_warnings
    )


def test_extract_dng_exif_payload_reads_payload_before_closing_image():
    """
    @brief Reproduce EXIF payload read failure after source image context closes.
    @details Builds fake EXIF object whose `tobytes` fails when invoked after
      source-image context exit; extractor must serialize payload and parse
      `DateTime` while image handle is still open.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-074, REQ-077
    """

    observed = {"closed": False}

    class _LazyExif:
        """@brief Provide EXIF object requiring open source handle for `tobytes`."""

        def __init__(self, state):
            self._state = state

        def get(self, key):
            if key == 274:
                return 6
            if key == 306:
                return "2004:08:28 16:04:14"
            return None

        def tobytes(self):
            if self._state["closed"]:
                raise ValueError("seek of closed file")
            return b"lazy-exif"

    class _FakeSourceImage:
        """@brief Provide fake source image with close-sensitive EXIF payload."""

        def __init__(self, state):
            self._state = state

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            self._state["closed"] = True
            return False

        def getexif(self):
            return _LazyExif(self._state)

    class _FakePilImageModule:
        """@brief Provide fake PIL module exposing deterministic `open`."""

        @staticmethod
        def open(_path):
            return _FakeSourceImage(observed)

    exif_payload, exif_timestamp, source_orientation = (
        dng2hdr2jpg._extract_dng_exif_payload_and_timestamp(
            pil_image_module=_FakePilImageModule,
            input_dng=Path("scene.dng"),
        )
    )

    assert exif_payload == b"lazy-exif"
    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2004:08:28 16:04:14"
    )
    assert exif_timestamp == expected_timestamp
    assert source_orientation == 6


def test_parse_exif_datetime_to_timestamp_accepts_exif_null_terminated_text():
    """
    @brief Reproduce EXIF datetime parsing failure with null-terminated payload.
    @details Validates parser behavior for EXIF datetime scalar ending with
      `\x00`; expected behavior requires successful parsing because EXIF tools
      may emit null-terminated ASCII strings.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-074
    """

    expected_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        "2024:07:08 09:10:11"
    )
    parsed_timestamp = dng2hdr2jpg._parse_exif_datetime_to_timestamp(
        b"2024:07:08 09:10:11\x00"
    )

    assert parsed_timestamp == expected_timestamp


def test_refresh_output_jpg_exif_thumbnail_normalizes_short_sequence_values(tmp_path):
    """
    @brief Reproduce EXIF dump crash on non-integer SHORT sequence values.
    @details Exercises EXIF thumbnail refresh with source EXIF payload containing
      a SHORT-sequence tag with a null-terminated ASCII bytes element and
      verifies the refresh path normalizes values before `piexif.dump`,
      preventing `struct.error`.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-077, REQ-078
    """

    observed = {"insert_calls": []}
    output_jpg = tmp_path / "scene.jpg"
    output_jpg.write_text("jpg", encoding="utf-8")

    class _FakeThumbnailImage:
        """@brief Provide fake Pillow image for deterministic thumbnail refresh."""

        mode = "RGB"

        def copy(self):
            """@brief Return self copy for orientation helper compatibility."""

            return self

        def thumbnail(self, _size):
            """@brief Accept thumbnail resize request without side effects."""

        def save(self, buffer, format, quality, optimize):
            """@brief Serialize deterministic thumbnail payload into buffer."""

            assert format == "JPEG"
            assert quality == 85
            assert optimize is True
            buffer.write(b"thumb")

    class _FakeOpenedImage(_FakeThumbnailImage):
        """@brief Provide context-manager wrapper for fake Pillow open call."""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

    class _FakePilImageModule:
        """@brief Provide fake PIL module exposing deterministic `open`."""

        class Transpose:
            """@brief Provide transpose constants required by orientation map."""

            FLIP_LEFT_RIGHT = 0
            ROTATE_180 = 1
            FLIP_TOP_BOTTOM = 2
            TRANSPOSE = 3
            ROTATE_270 = 4
            TRANSVERSE = 5
            ROTATE_90 = 6

        @staticmethod
        def open(path):
            assert Path(path).name == "scene.jpg"
            return _FakeOpenedImage()

    class _FakeImageIfd:
        """@brief Provide minimal EXIF tag constants used by production code."""

        Orientation = 274
        YCbCrSubSampling = 530

    class _FakePiexifModule:
        """@brief Provide deterministic piexif-like module for defect repro."""

        ImageIFD = _FakeImageIfd

        @staticmethod
        def load(_payload):
            return {
                "0th": {_FakeImageIfd.YCbCrSubSampling: (b"2\x00", "1")},
                "Exif": {},
                "GPS": {},
                "Interop": {},
                "1st": {},
                "thumbnail": None,
            }

        @staticmethod
        def dump(exif_dict):
            ycbcr_subsampling = exif_dict["0th"].get(_FakeImageIfd.YCbCrSubSampling)
            if ycbcr_subsampling != (2, 1):
                raise struct.error("required argument is not an integer")
            return b"exif-bytes"

        @staticmethod
        def insert(exif_bytes, output_path):
            observed["insert_calls"].append((exif_bytes, Path(output_path)))

    dng2hdr2jpg._refresh_output_jpg_exif_thumbnail_after_save(
        pil_image_module=_FakePilImageModule,
        piexif_module=_FakePiexifModule,
        output_jpg=output_jpg,
        source_exif_payload=b"source-exif",
        source_orientation=1,
    )

    assert observed["insert_calls"] == [(b"exif-bytes", output_jpg)]


def test_normalize_ifd_integer_like_values_flattens_nested_short_pairs():
    """
    @brief Reproduce piexif dump crash with nested SHORT pair tuples.
    @details Builds EXIF dictionary containing nested tuple values for a SHORT
      sequence tag and verifies normalization flattens two-item integer pairs
      into one flat tuple acceptable by `piexif.dump`.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-077, REQ-078
    """

    class _FakePiexifModule:
        """@brief Provide minimal piexif metadata table for SHORT sequence tag."""

        TAGS = {
            "0th": {
                50728: {"type": 3},
            },
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
        }

    exif_dict = {
        "0th": {
            50728: ((105991, 200000), (1, 1), (157481, 200000)),
        },
        "Exif": {},
        "GPS": {},
        "Interop": {},
        "1st": {},
    }

    dng2hdr2jpg._normalize_ifd_integer_like_values_for_piexif_dump(
        piexif_module=_FakePiexifModule,
        exif_dict=exif_dict,
    )

    assert 50728 not in exif_dict["0th"]


def test_normalize_ifd_integer_like_values_drops_out_of_range_short_values():
    """
    @brief Reproduce piexif dump crash with out-of-range SHORT sequence values.
    @details Builds EXIF dictionary with flattened SHORT sequence containing
      values above `65535` and verifies normalization drops that invalid tag to
      prevent `piexif.dump` unsigned-short range failures.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-077, REQ-078
    """

    class _FakePiexifModule:
        """@brief Provide minimal piexif metadata table for SHORT sequence tag."""

        TAGS = {
            "0th": {
                50728: {"type": 3},
            },
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
        }

    exif_dict = {
        "0th": {
            50728: (105991, 200000, 1, 1, 157481, 200000),
        },
        "Exif": {},
        "GPS": {},
        "Interop": {},
        "1st": {},
    }

    dng2hdr2jpg._normalize_ifd_integer_like_values_for_piexif_dump(
        piexif_module=_FakePiexifModule,
        exif_dict=exif_dict,
    )

    assert 50728 not in exif_dict["0th"]


def test_normalize_ifd_integer_like_values_converts_byte_tuple_to_bytes():
    """
    @brief Reproduce piexif type error for BYTE tags represented as tuples.
    @details Builds EXIF dictionary where BYTE-type tag `RawImageDigest` uses a
      tuple of integers and verifies normalization converts it to `bytes` for
      `piexif.dump` compatibility.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-077, REQ-078
    """

    class _FakePiexifModule:
        """@brief Provide minimal piexif metadata table for BYTE tag."""

        TAGS = {
            "0th": {
                50972: {"type": 7},
            },
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
        }

    exif_dict = {
        "0th": {
            50972: (38, 78, 96, 211),
        },
        "Exif": {},
        "GPS": {},
        "Interop": {},
        "1st": {},
    }

    dng2hdr2jpg._normalize_ifd_integer_like_values_for_piexif_dump(
        piexif_module=_FakePiexifModule,
        exif_dict=exif_dict,
    )

    assert exif_dict["0th"][50972] == bytes((38, 78, 96, 211))


def test_dng2hdr2jpg_skips_timestamp_update_when_exif_datetime_missing(
    monkeypatch, tmp_path
):
    """
    @brief Validate no timestamp update when EXIF datetime fields are absent.
    @details Runs enfuse flow with EXIF payload but without supported datetime
      tags and asserts JPEG EXIF copy remains active while `os.utime` is not
      called.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-074, REQ-077, REQ-078
    """

    observed = {
        "brights": [],
        "output_bps": [],
        "use_camera_wb": [],
        "no_auto_bright": [],
        "gamma": [],
        "utime_calls": [],
        "jpg_save": None,
        "refresh_calls": [],
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
        def get(key):
            if key == 274:
                return 8
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

        def save(
            self,
            path,
            format,
            quality=None,
            optimize=None,
            exif=None,
            compress_level=None,
        ):
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

    fake_piexif_module = object()

    def _fake_refresh_output_jpg_exif_thumbnail_after_save(
        pil_image_module,
        piexif_module,
        output_jpg,
        source_exif_payload,
        source_orientation,
    ):
        observed["refresh_calls"].append(
            {
                "pil_image_module": pil_image_module,
                "piexif_module": piexif_module,
                "output_jpg": Path(output_jpg),
                "source_exif_payload": source_exif_payload,
                "source_orientation": source_orientation,
            }
        )

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_load_image_dependencies",
        lambda: (
            _FakeRawPyModule,
            _FakeImageIoModule,
            _FakePilImageModule,
            _FakePilEnhanceModule,
        ),
    )
    monkeypatch.setattr(
        dng2hdr2jpg, "_load_piexif_dependency", lambda: fake_piexif_module
    )
    monkeypatch.setattr(
        dng2hdr2jpg,
        "_refresh_output_jpg_exif_thumbnail_after_save",
        _fake_refresh_output_jpg_exif_thumbnail_after_save,
    )
    monkeypatch.setattr(
        dng2hdr2jpg.shutil,
        "which",
        lambda cmd: "/usr/bin/enfuse" if cmd == "enfuse" else None,
    )
    monkeypatch.setattr(dng2hdr2jpg.subprocess, "run", _fake_subprocess_run)
    monkeypatch.setattr(dng2hdr2jpg.os, "utime", _fake_utime)

    input_dng = tmp_path / "scene.dng"
    input_dng.write_text("dng", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"

    result = dng2hdr2jpg.run(
        [str(input_dng), str(output_jpg), "--ev=2", "--enable-enfuse"]
    )

    assert result == 0
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert observed["jpg_save"]["exif"] == b"fake-exif-no-date"
    assert len(observed["refresh_calls"]) == 1
    assert observed["refresh_calls"][0]["piexif_module"] is fake_piexif_module
    assert observed["refresh_calls"][0]["output_jpg"] == output_jpg
    assert observed["refresh_calls"][0]["source_exif_payload"] == b"fake-exif-no-date"
    assert observed["refresh_calls"][0]["source_orientation"] == 8
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
    @satisfies TST-011, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-082, REQ-083, REQ-084, REQ-088, REQ-089, REQ-093, REQ-094, REQ-097
    """

    dng2hdr2jpg.print_help("0.0.0")
    captured = capsys.readouterr()
    output = captured.out
    operators_section = output.split("  Luminance operators:", 1)[1].split(
        "  Luminance operator main CLI controls:", 1
    )[0]

    assert "--enable-luminance" in output
    assert "--enable-enfuse" in output
    assert "--auto-ev" in output
    assert "--ev-zero=<value>" in output
    assert "--auto-zero" in output
    assert "--auto-zero-pct=<0..100>" in output
    assert "--auto-ev-pct=<0..100>" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AUTO_ZERO_PCT:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AUTO_EV_PCT:g}" in output
    assert "Fixed exposure bracket EV: 0.25 .. MAX_BRACKET in 0.25 steps" in output
    assert "MAX_BRACKET = ((bits_per_color-8)/2)-abs(ev_zero) from input DNG" in output
    assert "-SAFE_ZERO_MAX .. +SAFE_ZERO_MAX in 0.25 steps" in output
    assert "SAFE_ZERO_MAX = ((bits_per_color-8)/2)-1 from input DNG" in output
    assert "--gamma=<a,b>" in output
    assert "--post-gamma=<value>" in output
    assert "--brightness=<value>" in output
    assert "--contrast=<value>" in output
    assert "--saturation=<value>" in output
    assert "--auto-brightness" in output
    assert "--ab-target-grey=<(0,1)>" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AB_TARGET_GREY:g}" in output
    assert "--jpg-compression=<0..100>" in output
    assert "--auto-adjust" in output
    assert "--aa-blur-sigma=<value>" in output
    assert "--aa-blur-threshold-pct=<0..100>" in output
    assert "--aa-level-low-pct=<0..100>" in output
    assert "--aa-level-high-pct=<0..100>" in output
    assert "--aa-sigmoid-contrast=<value>" in output
    assert "--aa-sigmoid-midpoint=<0..1>" in output
    assert "--aa-saturation-gamma=<value>" in output
    assert "--aa-highpass-blur-sigma=<value>" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_BLUR_SIGMA:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_BLUR_THRESHOLD_PCT:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_LEVEL_LOW_PCT:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_LEVEL_HIGH_PCT:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_SIGMOID_CONTRAST:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_SIGMOID_MIDPOINT:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_SATURATION_GAMMA:g}" in output
    assert f"default: {dng2hdr2jpg.DEFAULT_AA_HIGHPASS_BLUR_SIGMA:g}" in output
    assert "--luminance-hdr-model=<name>" in output
    assert "--luminance-hdr-weight=<name>" in output
    assert "--luminance-hdr-response-curve=<name>" in output
    assert "--luminance-tmo=<name>" in output
    assert "default: mantiuk08" in output
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


def test_dng2hdr2jpg_applies_postprocess_controls_and_quality_mapping(
    monkeypatch, tmp_path
):
    """
    @brief Validate shared postprocess controls and JPEG quality mapping.
    @details Executes encode path with non-default gamma/brightness/contrast/
      saturation factors and verifies fake Pillow operations and quality value.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066, REQ-073, REQ-078
    """

    observed = {"refresh_calls": []}

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for postprocess assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for conversion and postprocess."""

            assert Path(path).name == "merged_hdr.tif"
            return _FakeImage16()

    fake_piexif_module = object()

    def _fake_refresh_output_jpg_exif_thumbnail_after_save(
        pil_image_module,
        piexif_module,
        output_jpg,
        source_exif_payload,
        source_orientation,
    ):
        observed["refresh_calls"].append(
            {
                "pil_image_module": pil_image_module,
                "piexif_module": piexif_module,
                "output_jpg": Path(output_jpg),
                "source_exif_payload": source_exif_payload,
                "source_orientation": source_orientation,
            }
        )

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_refresh_output_jpg_exif_thumbnail_after_save",
        _fake_refresh_output_jpg_exif_thumbnail_after_save,
    )

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
        piexif_module=fake_piexif_module,
        source_exif_payload=b"source-exif",
        source_orientation=3,
    )

    assert "gamma" in observed["postprocess_ops"]
    assert ("brightness", 1.1) in observed["postprocess_ops"]
    assert ("contrast", 0.9) in observed["postprocess_ops"]
    assert ("saturation", 1.3) in observed["postprocess_ops"]
    jpg_save = observed["jpg_save"]
    assert isinstance(jpg_save, dict)
    assert jpg_save.get("quality") == 20
    assert len(observed["refresh_calls"]) == 1
    assert observed["refresh_calls"][0]["piexif_module"] is fake_piexif_module
    assert observed["refresh_calls"][0]["output_jpg"] == output_jpg
    assert observed["refresh_calls"][0]["source_exif_payload"] == b"source-exif"
    assert observed["refresh_calls"][0]["source_orientation"] == 3
    assert output_jpg.exists()


def test_dng2hdr2jpg_keeps_static_postprocess_independent_from_ev_zero(tmp_path):
    """
    @brief Validate static postprocess factors are not modified by `ev_zero`.
    @details Executes `_encode_jpg` with `ev_zero=-1` and non-default static
      factors, then verifies only configured static brightness/contrast/
      saturation factors are applied.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-095
    """

    observed = {"postprocess_ops": [], "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake `imageio` module for ev-zero postprocess assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake 16-bit payload for merged HDR source."""

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
            post_gamma=1.0,
            brightness=1.2,
            contrast=0.9,
            saturation=1.1,
            jpg_compression=10,
        ),
        ev_zero=-1.0,
    )

    assert observed["postprocess_ops"] == [
        ("brightness", 1.2),
        ("contrast", 0.9),
        ("saturation", 1.1),
    ]
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_applies_auto_adjust_pipeline_only_when_enabled(
    monkeypatch, tmp_path
):
    """
    @brief Validate auto-adjust-stage execution only when explicitly enabled.
    @details Executes encode path with `auto_adjust_mode="ImageMagick"`, captures ImageMagick
      command vectors, and verifies two-step auto-adjust flow over temporary files
      (`postprocessed_input.tif` then `auto_adjust_output.tif`) before final JPEG save.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-065, REQ-066, REQ-073, REQ-086
    """

    observed = {"commands": [], "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for auto-adjust encode assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake payload for merged/auto-adjust TIFF paths."""

            if Path(path).name == "auto_adjust_output.tif":

                class _FakeAutoAdjustPayload:
                    mode = "RGB"

                return _FakeAutoAdjustPayload()
            return _FakeImage16()

    def _fake_subprocess_run(command, check):
        """@brief Capture auto-adjust subprocess calls and materialize outputs."""

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
            auto_adjust_mode="ImageMagick",
            auto_adjust_options=dng2hdr2jpg.AutoAdjustOptions(
                blur_sigma=1.7,
                blur_threshold_pct=8.5,
                level_low_pct=1.2,
                level_high_pct=97.8,
                sigmoid_contrast=4.4,
                sigmoid_midpoint=0.42,
                saturation_gamma=0.77,
                highpass_blur_sigma=3.6,
            ),
        ),
    )

    assert len(observed["commands"]) == 2
    assert observed["commands"][0][0] == "magick"
    assert observed["commands"][1][0] == "magick"
    assert Path(observed["commands"][0][-1]).name == "auto_adjust_input_16.tif"
    assert Path(observed["commands"][1][-1]).name == "auto_adjust_output.tif"
    assert observed["commands"][1][5] == "0x1.7+8.5%"
    assert observed["commands"][1][9] == "1.2%,97.8%"
    assert observed["commands"][1][12] == "4.4x42%"
    assert observed["commands"][1][18] == "0.77"
    assert observed["commands"][1][28] == "0x3.6"
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_applies_opencv_auto_adjust_pipeline_when_selected(
    monkeypatch, tmp_path
):
    """
    @brief Validate OpenCV auto-adjust-stage dispatch when auto-adjust mode is `OpenCV`.
    @details Executes encode path with `auto_adjust_mode="OpenCV"`, injects fake OpenCV
      dependency tuple, and verifies OpenCV auto-adjust function receives expected
      temporary input/output TIFF paths before final JPEG save.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-073, REQ-075, REQ-087
    """

    observed = {"opencv_call": {}, "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for OpenCV auto-adjust dispatch test."""

        @staticmethod
        def imread(path):
            """@brief Return fake payload for merged/auto-adjust TIFF reads."""

            if Path(path).name == "auto_adjust_output.tif":

                class _FakeAutoAdjustPayload:
                    mode = "RGB"

                return _FakeAutoAdjustPayload()
            return _FakeImage16()

    def _fake_apply_validated_auto_adjust_pipeline_opencv(
        input_file, output_file, cv2_module, np_module, auto_adjust_options
    ):
        """@brief Capture OpenCV auto-adjust dispatch parameters and materialize output."""

        observed["opencv_call"] = {
            "input": Path(input_file).name,
            "output": Path(output_file).name,
            "cv2": cv2_module,
            "np": np_module,
            "options": auto_adjust_options,
        }
        Path(output_file).write_text("auto-adjust", encoding="utf-8")

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_apply_validated_auto_adjust_pipeline_opencv",
        _fake_apply_validated_auto_adjust_pipeline_opencv,
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
            auto_adjust_mode="OpenCV",
            auto_adjust_options=dng2hdr2jpg.AutoAdjustOptions(
                blur_sigma=1.8,
                blur_threshold_pct=11.0,
                level_low_pct=0.2,
                level_high_pct=99.0,
                sigmoid_contrast=3.5,
                sigmoid_midpoint=0.55,
                saturation_gamma=0.82,
                highpass_blur_sigma=2.8,
            ),
        ),
        auto_adjust_opencv_dependencies=(fake_cv2_module, fake_numpy_module),
    )

    assert observed["opencv_call"] is not None
    assert observed["opencv_call"]["input"] == "postprocessed_input.tif"
    assert observed["opencv_call"]["output"] == "auto_adjust_output.tif"
    assert observed["opencv_call"]["cv2"] is fake_cv2_module
    assert observed["opencv_call"]["np"] is fake_numpy_module
    assert observed["opencv_call"]["options"] == dng2hdr2jpg.AutoAdjustOptions(
        blur_sigma=1.8,
        blur_threshold_pct=11.0,
        level_low_pct=0.2,
        level_high_pct=99.0,
        sigmoid_contrast=3.5,
        sigmoid_midpoint=0.55,
        saturation_gamma=0.82,
        highpass_blur_sigma=2.8,
    )
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_applies_auto_brightness_before_static_postprocess(monkeypatch, tmp_path):
    """
    @brief Validate auto-brightness runs before static postprocess operations.
    @details Executes `_encode_jpg` with enabled auto-brightness, captures
      dispatch call and static enhancement factors, and verifies static factors
      are applied after auto-brightness output generation.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-066, REQ-090
    """

    observed = {"auto_brightness": None, "postprocess_ops": [], "jpg_save": None}

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for auto-brightness encode assertions."""

        @staticmethod
        def imread(path):
            """@brief Return fake payload for merged TIFF input."""

            del path
            numpy_module = __import__("numpy")
            return numpy_module.zeros((2, 2, 3), dtype=numpy_module.uint16)

    def _fake_apply_auto_brightness_rgb_uint8(
        cv2_module, np_module, image_rgb_uint8, auto_brightness_options
    ):
        """@brief Capture auto-brightness invocation and return payload marker."""

        observed["auto_brightness"] = {
            "cv2": cv2_module,
            "np": np_module,
            "dtype": str(getattr(image_rgb_uint8, "dtype", "")),
            "options": auto_brightness_options,
        }

        class _FakeAutoBrightnessOutput:
            mode = "RGB"

        return _FakeAutoBrightnessOutput()

    monkeypatch.setattr(
        dng2hdr2jpg,
        "_apply_auto_brightness_rgb_uint8",
        _fake_apply_auto_brightness_rgb_uint8,
    )

    merged_tiff = tmp_path / "merged_hdr.tif"
    merged_tiff.write_text("merged", encoding="utf-8")
    output_jpg = tmp_path / "scene.jpg"
    pil_image_module, pil_enhance_module = _build_fake_pillow_modules(observed)
    fake_cv2_module = object()
    fake_numpy_module = __import__("numpy")

    dng2hdr2jpg._encode_jpg(
        imageio_module=_FakeImageIoModule,
        pil_image_module=pil_image_module,
        pil_enhance_module=pil_enhance_module,
        merged_tiff=merged_tiff,
        output_jpg=output_jpg,
        postprocess_options=dng2hdr2jpg.PostprocessOptions(
            post_gamma=1.0,
            brightness=1.3,
            contrast=0.9,
            saturation=1.1,
            jpg_compression=10,
            auto_brightness_enabled=True,
            auto_brightness_options=dng2hdr2jpg.AutoBrightnessOptions(target_grey=0.22),
        ),
        auto_adjust_opencv_dependencies=(fake_cv2_module, fake_numpy_module),
    )

    assert observed["auto_brightness"] is not None
    assert observed["auto_brightness"]["cv2"] is fake_cv2_module
    assert observed["auto_brightness"]["np"] is fake_numpy_module
    assert observed["auto_brightness"]["dtype"] == "uint16"
    assert observed["auto_brightness"]["options"] == dng2hdr2jpg.AutoBrightnessOptions(target_grey=0.22)
    assert observed["postprocess_ops"] == [
        ("brightness", 1.3),
        ("contrast", 0.9),
        ("saturation", 1.1),
    ]
    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()


def test_dng2hdr2jpg_auto_brightness_uses_bt709_luminance_gain():
    """
    @brief Validate auto-brightness applies one linear-domain global gain.
    @details Runs auto-brightness on uint16 RGB input and verifies that decoded
      linear-domain per-channel gains remain equal per pixel.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-090, REQ-099
    """

    numpy_module = __import__("numpy")
    input_image = numpy_module.array(
        [
            [[8000, 16000, 24000], [10000, 20000, 30000]],
            [[12000, 24000, 36000], [9000, 18000, 27000]],
        ],
        dtype=numpy_module.uint16,
    )
    output_image = dng2hdr2jpg._apply_auto_brightness_rgb_uint8(
        cv2_module=object(),
        np_module=numpy_module,
        image_rgb_uint8=input_image,
        auto_brightness_options=dng2hdr2jpg.AutoBrightnessOptions(target_grey=0.22),
    )
    assert output_image.dtype == numpy_module.uint16
    assert output_image.shape == input_image.shape

    input_linear = dng2hdr2jpg._to_linear_srgb(
        np_module=numpy_module,
        image_srgb=input_image.astype(numpy_module.float64) / 65535.0,
    )
    output_linear = dng2hdr2jpg._to_linear_srgb(
        np_module=numpy_module,
        image_srgb=output_image.astype(numpy_module.float64) / 65535.0,
    )
    epsilon = 1e-8
    gain_r = output_linear[..., 0] / (input_linear[..., 0] + epsilon)
    gain_g = output_linear[..., 1] / (input_linear[..., 1] + epsilon)
    gain_b = output_linear[..., 2] / (input_linear[..., 2] + epsilon)
    assert numpy_module.max(numpy_module.abs(gain_r - gain_g)) < 2e-2
    assert numpy_module.max(numpy_module.abs(gain_r - gain_b)) < 2e-2


def test_dng2hdr2jpg_auto_brightness_caps_gain_to_max_gain():
    """
    @brief Validate auto-brightness gain cap prevents over-amplification.
    @details Uses very dark input and verifies effective amplification does not exceed
      configured fixed cap `DEFAULT_AB_MAX_GAIN` before transfer and quantization.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-088, REQ-090
    """

    numpy_module = __import__("numpy")
    input_image = numpy_module.full((2, 2, 3), 500, dtype=numpy_module.uint16)
    output_image = dng2hdr2jpg._apply_auto_brightness_rgb_uint8(
        cv2_module=object(),
        np_module=numpy_module,
        image_rgb_uint8=input_image,
        auto_brightness_options=dng2hdr2jpg.AutoBrightnessOptions(target_grey=0.9),
    )
    ratio = float(output_image[0, 0, 1]) / float(input_image[0, 0, 1])
    assert ratio <= dng2hdr2jpg.DEFAULT_AB_MAX_GAIN * 1.1


def test_dng2hdr2jpg_auto_brightness_rejects_non_uint16_input():
    """
    @brief Validate auto-brightness rejects non-uint16 payloads.
    @details Executes algorithm with uint8 tensor and verifies deterministic
      validation error.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-090
    """

    numpy_module = __import__("numpy")
    input_image = numpy_module.zeros((2, 2, 3), dtype=numpy_module.uint8)
    with pytest.raises(ValueError):
        dng2hdr2jpg._apply_auto_brightness_rgb_uint8(
            cv2_module=object(),
            np_module=numpy_module,
            image_rgb_uint8=input_image,
            auto_brightness_options=dng2hdr2jpg.AutoBrightnessOptions(target_grey=0.18),
        )


def test_dng2hdr2jpg_opencv_auto_adjust_accepts_uint8_input_by_upconverting(tmp_path):
    """
    @brief Reproduce OpenCV auto-adjust failure when auto-adjust input TIFF is decoded as uint8.
    @details Executes `_apply_validated_auto_adjust_pipeline_opencv` with fake cv2 read
      path returning `uint8` 3-channel image and expects deterministic in-function
      promotion to `uint16` before float-domain pipeline execution.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-073, REQ-075, REQ-087
    """

    numpy_module = __import__("numpy")

    class _FakeCv2Module:
        """@brief Provide minimal cv2 surface for uint8 OpenCV auto-adjust reproducer."""

        IMREAD_UNCHANGED = -1
        COLOR_BGR2RGB = 10
        COLOR_RGB2BGR = 11
        BORDER_REFLECT = 12

        def __init__(self):
            self.written = None

        def imread(self, path, mode):
            """@brief Return deterministic uint8 auto-adjust input tensor."""

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
            Path(path).write_text("auto-adjust-output", encoding="utf-8")
            return True

    input_tiff = tmp_path / "postprocessed_input.tif"
    input_tiff.write_text("payload", encoding="utf-8")
    output_tiff = tmp_path / "auto_adjust_output.tif"
    fake_cv2_module = _FakeCv2Module()

    dng2hdr2jpg._apply_validated_auto_adjust_pipeline_opencv(
        input_file=input_tiff,
        output_file=output_tiff,
        cv2_module=fake_cv2_module,
        np_module=numpy_module,
        auto_adjust_options=dng2hdr2jpg.AutoAdjustOptions(),
    )

    assert fake_cv2_module.written is not None
    assert fake_cv2_module.written["path"] == "auto_adjust_output.tif"
    assert fake_cv2_module.written["dtype"] == "uint16"
    assert fake_cv2_module.written["shape"] == (2, 2, 3)
    assert output_tiff.exists()


def test_dng2hdr2jpg_opencv_auto_adjust_accepts_shared_knob_values_on_synthetic_fixture(
    tmp_path,
):
    """
    @brief Validate OpenCV auto-adjust numeric pathway accepts shared knob values.
    @details Executes OpenCV auto-adjust over deterministic synthetic `uint16`
      fixture with defaults and with custom shared knobs, asserting stable output
      shape/dtype bounds and successful write on both runs.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-083, REQ-087
    """

    numpy_module = __import__("numpy")

    class _FixtureCv2Module:
        """@brief Provide deterministic cv2 surface for synthetic fixture execution."""

        IMREAD_UNCHANGED = -1
        COLOR_BGR2RGB = 10
        COLOR_RGB2BGR = 11
        BORDER_REFLECT = 12

        def __init__(self):
            self.written_payloads = []

        @staticmethod
        def imread(path, mode):
            """@brief Return deterministic synthetic `uint16` tensor."""

            del path
            assert mode == _FixtureCv2Module.IMREAD_UNCHANGED
            return numpy_module.array(
                [
                    [[1200, 2100, 3200], [4200, 5300, 6400]],
                    [[7400, 8500, 9600], [10600, 11700, 12800]],
                ],
                dtype=numpy_module.uint16,
            )

        @staticmethod
        def cvtColor(image, code):
            """@brief Apply deterministic channel reorder conversion."""

            if code in (
                _FixtureCv2Module.COLOR_BGR2RGB,
                _FixtureCv2Module.COLOR_RGB2BGR,
            ):
                return image[..., ::-1]
            raise AssertionError(f"Unexpected conversion code: {code}")

        @staticmethod
        def GaussianBlur(image, ksize, sigmaX, sigmaY, borderType):
            """@brief Return deterministic no-op blur tensor."""

            del ksize, sigmaX, sigmaY
            assert borderType == _FixtureCv2Module.BORDER_REFLECT
            return image

        def imwrite(self, path, payload):
            """@brief Capture output tensor metadata and persist artifact."""

            self.written_payloads.append(
                {
                    "path": Path(path).name,
                    "dtype": str(payload.dtype),
                    "shape": payload.shape,
                    "min": int(payload.min()),
                    "max": int(payload.max()),
                }
            )
            Path(path).write_text("auto-adjust-output", encoding="utf-8")
            return True

    input_tiff = tmp_path / "postprocessed_input.tif"
    input_tiff.write_text("payload", encoding="utf-8")
    output_default = tmp_path / "auto_adjust_output_default.tif"
    output_custom = tmp_path / "auto_adjust_output_custom.tif"
    fake_cv2_module = _FixtureCv2Module()

    dng2hdr2jpg._apply_validated_auto_adjust_pipeline_opencv(
        input_file=input_tiff,
        output_file=output_default,
        cv2_module=fake_cv2_module,
        np_module=numpy_module,
        auto_adjust_options=dng2hdr2jpg.AutoAdjustOptions(),
    )
    dng2hdr2jpg._apply_validated_auto_adjust_pipeline_opencv(
        input_file=input_tiff,
        output_file=output_custom,
        cv2_module=fake_cv2_module,
        np_module=numpy_module,
        auto_adjust_options=dng2hdr2jpg.AutoAdjustOptions(
            blur_sigma=1.3,
            blur_threshold_pct=7.0,
            level_low_pct=0.5,
            level_high_pct=98.0,
            sigmoid_contrast=2.5,
            sigmoid_midpoint=0.45,
            saturation_gamma=0.9,
            highpass_blur_sigma=1.9,
        ),
    )

    assert len(fake_cv2_module.written_payloads) == 2
    for payload in fake_cv2_module.written_payloads:
        assert payload["dtype"] == "uint16"
        assert payload["shape"] == (2, 2, 3)
        assert 0 <= payload["min"] <= 65535
        assert 0 <= payload["max"] <= 65535
    assert output_default.exists()
    assert output_custom.exists()


def test_dng2hdr2jpg_auto_adjust_uint16_output_is_normalized_before_fromarray(
    monkeypatch, tmp_path
):
    """
    @brief Reproduce auto-adjust-path crash when ImageMagick output is uint16 RGB payload.
    @details Simulates auto-adjust output decode as `uint16` data and enforces a strict
      fake `Image.fromarray` contract that rejects non-`uint8` payload, matching
      observed Pillow failure; expected behavior is successful normalization before
      `fromarray`.
    @param monkeypatch {pytest.MonkeyPatch} Runtime patch helper.
    @param tmp_path {Path} Isolated filesystem fixture.
    @return {None} Assertions only.
    @satisfies TST-011, REQ-058, REQ-066, REQ-073, REQ-086
    """

    observed = {"jpg_save": None, "commands": []}

    class _FakeAutoAdjustScaled:
        """@brief Provide clip/astype chain for auto-adjust uint16 normalization."""

        def clip(self, _low, _high):
            """@brief Return self for deterministic clipping chain."""

            return self

        def astype(self, dtype):
            """@brief Return uint8 payload marker after normalization."""

            assert dtype == "uint8"

            class _FakeAutoAdjustUint8Payload:
                mode = "RGB"
                dtype = "uint8"

            return _FakeAutoAdjustUint8Payload()

    class _FakeAutoAdjustU16Payload:
        """@brief Emulate auto-adjust output payload with uint16 dtype."""

        dtype = "uint16"

        def __truediv__(self, value):
            """@brief Emulate normalization division branch."""

            assert value == 257.0
            return _FakeAutoAdjustScaled()

    class _FakeImageIoModule:
        """@brief Provide fake imageio module for auto-adjust uint16 reproducer."""

        @staticmethod
        def imread(path):
            """@brief Return base and auto-adjust payloads for encode path."""

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
            if Path(path).name == "auto_adjust_output.tif":
                return _FakeAutoAdjustU16Payload()
            return _FakeImage16()

    class _StrictPilImageModule:
        """@brief Fake PIL module that fails on non-uint8 fromarray payload."""

        @staticmethod
        def fromarray(payload):
            """@brief Enforce uint8-only conversion to reproduce original crash."""

            if getattr(payload, "dtype", None) != "uint8":
                raise TypeError(
                    f"Cannot handle this data type: {getattr(payload, 'dtype', None)}"
                )

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
        """@brief Emulate successful auto-adjust subprocess output materialization."""

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
            auto_adjust_mode="ImageMagick",
        ),
    )

    assert observed["jpg_save"] is not None
    assert observed["jpg_save"]["format"] == "JPEG"
    assert output_jpg.exists()
