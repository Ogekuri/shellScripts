#!/usr/bin/env python3
"""@brief Convert one DNG file into one HDR-merged JPG output.

@details Implements bracketed RAW extraction with three synthetic exposures
(`-ev`, `0`, `+ev`), merges them through selected `enfuse` or selected
`luminance-hdr-cli` flow with deterministic HDR model parameters, then writes
final JPG to user-selected output path. Temporary artifacts are isolated in a
temporary directory and removed automatically on success and failure.
    @satisfies PRJ-003, DES-008, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from shell_scripts.utils import (
    get_runtime_os,
    print_error,
    print_info,
    print_success,
)

PROGRAM = "shellscripts"
DESCRIPTION = "Convert DNG to HDR-merged JPG with optional luminance-hdr-cli backend."
DEFAULT_EV = 2.0
DEFAULT_GAMMA = (2.222, 4.5)
DEFAULT_POST_GAMMA = 1.0
DEFAULT_BRIGHTNESS = 1.0
DEFAULT_CONTRAST = 1.0
DEFAULT_SATURATION = 1.0
DEFAULT_JPG_COMPRESSION = 15
DEFAULT_LUMINANCE_HDR_MODEL = "debevec"
DEFAULT_LUMINANCE_HDR_WEIGHT = "flat"
DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE = "srgb"
DEFAULT_LUMINANCE_TMO = "reinhard02"
DEFAULT_REINHARD02_BRIGHTNESS = 1.25
DEFAULT_REINHARD02_CONTRAST = 0.85
DEFAULT_REINHARD02_SATURATION = 0.55
SUPPORTED_EV_VALUES = (0.5, 1.0, 1.5, 2.0)
_RUNTIME_OS_LABELS = {
    "windows": "Windows",
    "darwin": "MacOS",
}
_LUMINANCE_OPERATOR_TABLE_HEADERS = (
    "Operator",
    "Family / idea",
    "Character / typical result",
)
_LUMINANCE_OPERATOR_TABLE_SECONDARY_HEADER = ("", "Neutrality", "When to use")
_LUMINANCE_OPERATOR_TABLE_ENTRIES = (
    (
        "`ashikhmin`",
        "Local HVS-inspired tone mapping",
        "Natural local contrast, detail-preserving",
        "Medium",
        "Natural-looking local adaptation with preserved detail",
    ),
    (
        "`drago`",
        "Adaptive logarithmic compression",
        "Smooth, simple, highlight-friendly",
        "Medium",
        "Fast global compression of very wide dynamic range",
    ),
    (
        "`durand`",
        "Bilateral base/detail decomposition",
        "Soft local compression, photographic look",
        "Low-Medium",
        "Controlled local contrast compression",
    ),
    (
        "`fattal`",
        "Gradient-domain compression",
        "Strong detail enhancement, dramatic HDR",
        "Low",
        "Detail-heavy, stylized rendering",
    ),
    (
        "`ferradans`",
        "Perception-inspired adaptation + local contrast",
        "Realistic but locally adaptive",
        "Low-Medium",
        "Perceptual rendering with local contrast recovery",
    ),
    (
        "`ferwerda`",
        "Perceptually based visibility / adaptation",
        "Vision-model oriented, scene-visibility focused",
        "Medium",
        "Research / perceptual-visibility oriented rendering",
    ),
    (
        "`kimkautz`",
        "Consistent global tone reproduction",
        "Stable, consistent, restrained",
        "Medium-High",
        "Consistent results across different HDR images",
    ),
    (
        "`pattanaik`",
        "Human visual system adaptation model",
        "Perceptual, adaptive, scene-aware",
        "Low-Medium",
        "HVS-inspired tone mapping with rod/cone adaptation",
    ),
    (
        "`reinhard02`",
        "Photographic tone reproduction",
        "Natural, controllable, predictable",
        "High",
        "Best baseline when you want a relatively neutral operator",
    ),
    (
        "`reinhard05`",
        "Visual adaptation / photoreceptor model",
        "Natural but more adaptive than `reinhard02`",
        "Medium",
        "Simple controls with a perceptual/natural look",
    ),
    (
        "`mai`",
        "Fast effective tone mapping",
        "Clean, practical, generally easy to use",
        "Medium",
        "Quick all-purpose rendering with minimal tuning",
    ),
    (
        "`mantiuk06`",
        "Contrast mapping with detail enhancement",
        "Punchy, detailed, classic \"HDR\" look",
        "Low",
        "Strong detail and local contrast enhancement",
    ),
    (
        "`mantiuk08`",
        "Display-adaptive contrast mapping",
        "Perceptual, display-oriented, refined",
        "Low-Medium",
        "Optimizing HDR for display appearance",
    ),
    (
        "`vanhateren`",
        "Retina-inspired visual adaptation",
        "Vision-model based, adaptive",
        "Medium",
        "Retina-style perceptual adaptation experiments",
    ),
    (
        "`lischinski`",
        "Optimization-based local tonal adjustment",
        "Local, edge-aware, selective adjustments",
        "Low",
        "Local tonal manipulation with strong edge preservation",
    ),
)
_LUMINANCE_CONTROL_TABLE_HEADERS = (
    "Operator",
    "Main CLI controls",
)
_LUMINANCE_CONTROL_TABLE_ROWS = (
    ("`ashikhmin`", "`--tmoAshEq2`, `--tmoAshSimple`, `--tmoAshLocal`"),
    ("`drago`", "`--tmoDrgBias`"),
    ("`durand`", "`--tmoDurSigmaS`, `--tmoDurSigmaR`, `--tmoDurBase`"),
    ("`fattal`", "`--tmoFatAlpha`, `--tmoFatBeta`, `--tmoFatColor`, `--tmoFatNoise`, `--tmoFatNew`"),
    ("`ferradans`", "`--tmoFerRho`, `--tmoFerInvAlpha`"),
    ("`kimkautz`", "`--tmoKimKautzC1`, `--tmoKimKautzC2`"),
    ("`pattanaik`", "`--tmoPatMultiplier`, `--tmoPatLocal`, `--tmoPatAutoLum`, `--tmoPatCone`, `--tmoPatRod`"),
    ("`reinhard02`", "`--tmoR02Key`, `--tmoR02Phi`, `--tmoR02Scales`, `--tmoR02Num`, `--tmoR02Low`, `--tmoR02High`"),
    ("`reinhard05`", "`--tmoR05Brightness`, `--tmoR05Chroma`, `--tmoR05Lightness`"),
    ("`mantiuk06`", "`--tmoM06Contrast`, `--tmoM06Saturation`, `--tmoM06Detail`, `--tmoM06ContrastEqual`"),
    ("`mantiuk08`", "`--tmoM08ColorSaturation`, `--tmoM08ConstrastEnh`, `--tmoM08LuminanceLvl`, `--tmoM08SetLuminance`"),
    ("`vanhateren`", "`--tmoVanHaterenPupilArea`"),
    ("`lischinski`", "`--tmoLischinskiAlpha`"),
)


@dataclass(frozen=True)
class PostprocessOptions:
    """@brief Hold deterministic postprocessing option values.

    @details Encapsulates correction factors and JPEG compression level used by
    shared TIFF-to-JPG postprocessing for both HDR backends.
    @param post_gamma {float} Gamma correction factor for postprocessing stage.
    @param brightness {float} Brightness enhancement factor.
    @param contrast {float} Contrast enhancement factor.
    @param saturation {float} Saturation enhancement factor.
    @param jpg_compression {int} JPEG compression level in range `[0, 100]`.
    @param wow_mode {str|None} Optional wow implementation selector (`ImageMagick` or `OpenCV`).
    @return {None} Immutable dataclass container.
    @satisfies REQ-065, REQ-066, REQ-069, REQ-071, REQ-072, REQ-073, REQ-075
    """

    post_gamma: float
    brightness: float
    contrast: float
    saturation: float
    jpg_compression: int
    wow_mode: str | None = None


@dataclass(frozen=True)
class LuminanceOptions:
    """@brief Hold deterministic luminance-hdr-cli option values.

    @details Encapsulates luminance backend model and tone-mapping parameters
    forwarded to `luminance-hdr-cli` command generation.
    @param hdr_model {str} Luminance HDR model (`--hdrModel`).
    @param hdr_weight {str} Luminance weighting function (`--hdrWeight`).
    @param hdr_response_curve {str} Luminance response curve (`--hdrResponseCurve`).
    @param tmo {str} Tone-mapping operator (`--tmo`).
    @param tmo_extra_args {tuple[str, ...]} Explicit passthrough `--tmo*` option pairs in CLI order.
    @return {None} Immutable dataclass container.
    @satisfies REQ-061, REQ-067, REQ-068
    """

    hdr_model: str
    hdr_weight: str
    hdr_response_curve: str
    tmo: str
    tmo_extra_args: tuple[str, ...]


def _print_box_table(headers, rows, header_rows=()):
    """@brief Print one Unicode box-drawing table.

    @details Computes deterministic column widths from headers and rows, then
    prints aligned borders and cells using Unicode line-drawing glyphs.
    @param headers {tuple[str, ...]} Table header labels in fixed output order.
    @param header_rows {tuple[tuple[str, ...], ...]} Additional physical header rows rendered before header/body separator.
    @param rows {tuple[tuple[str, ...], ...]} Table body rows with one value per column.
    @return {None} Writes formatted table to stdout.
    @satisfies REQ-070
    """

    widths = [len(header) for header in headers]
    for header_row in header_rows:
        for idx, value in enumerate(header_row):
            widths[idx] = max(widths[idx], len(value))
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    def _border(left, middle, right):
        return left + middle.join("─" * (width + 2) for width in widths) + right

    def _line(values):
        cells = [f" {value.ljust(widths[idx])} " for idx, value in enumerate(values)]
        return "│" + "│".join(cells) + "│"

    print(_border("┌", "┬", "┐"))
    print(_line(headers))
    for header_row in header_rows:
        print(_line(header_row))
    print(_border("├", "┼", "┤"))
    for row in rows:
        print(_line(row))
    print(_border("└", "┴", "┘"))


def _build_two_line_operator_rows(operator_entries):
    """@brief Build two-line physical rows for luminance operator table.

    @details Expands each logical operator entry into two physical rows while
    preserving the bordered three-column layout used by help rendering.
    @param operator_entries {tuple[tuple[str, str, str, str, str], ...]} Logical operator rows in `(operator, family, character, neutrality, when_to_use)` format.
    @return {tuple[tuple[str, str, str], ...]} Expanded physical rows for `_print_box_table`.
    @satisfies REQ-070
    """

    rows = []
    for operator, family, character, neutrality, when_to_use in operator_entries:
        rows.append((operator, family, character))
        rows.append(("", neutrality, when_to_use))
    return tuple(rows)


def print_help(version):
    """@brief Print help text for the `dng2hdr2jpg` command.

    @details Documents required positional arguments, optional EV/RAW gamma
    controls, shared postprocessing controls, backend selection, and
    luminance-hdr-cli tone-mapping options.
    @param version {str} CLI version label to append in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-075
    """

    print(
        f"Usage: {PROGRAM} dng2hdr2jpg <input.dng> <output.jpg> "
        f"[--ev=<value>] [--gamma=<a,b>] [--post-gamma=<value>] "
        f"[--brightness=<value>] [--contrast=<value>] [--saturation=<value>] "
        f"[--jpg-compression=<0..100>] [--wow <ImageMagick|OpenCV>] (--enable-enfuse | --enable-luminance) "
        f"[--luminance-hdr-model=<name>] [--luminance-hdr-weight=<name>] "
        f"[--luminance-hdr-response-curve=<name>] [--luminance-tmo=<name>] "
        f"[--tmo*=<value>] ({version})"
    )
    print()
    print("dng2hdr2jpg options:")
    print("  <input.dng>      - Input DNG file (required).")
    print("  <output.jpg>     - Output JPG file (required).")
    print("  --ev=<value>     - Exposure bracket EV: 0.5 | 1 | 1.5 | 2 (default: 2).")
    print(f"  --gamma=<a,b>    - RAW extraction gamma pair (default: {DEFAULT_GAMMA[0]},{DEFAULT_GAMMA[1]}).")
    print("                     Example: --gamma=1,1 for linear extraction.")
    print("  --post-gamma=<value> - Postprocess gamma correction factor (backend-default when omitted).")
    print("  --brightness=<value> - Postprocess brightness factor (backend-default when omitted).")
    print("  --contrast=<value>   - Postprocess contrast factor (backend-default when omitted).")
    print("  --saturation=<value> - Postprocess saturation factor (backend-default when omitted).")
    print(f"  --jpg-compression=<0..100> - JPEG compression level (default: {DEFAULT_JPG_COMPRESSION}).")
    print("  --wow <name>     - Enable wow stage implementation (`ImageMagick` or `OpenCV`).")
    print("  --enable-enfuse")
    print("                   - Select enfuse backend (required, mutually exclusive with --enable-luminance).")
    print("  --enable-luminance")
    print("                   - Select luminance-hdr-cli backend (required, mutually exclusive with --enable-enfuse).")
    print(
        "  [postprocess defaults]"
        f" - --enable-enfuse: post-gamma={DEFAULT_POST_GAMMA}, brightness={DEFAULT_BRIGHTNESS},"
        f" contrast={DEFAULT_CONTRAST}, saturation={DEFAULT_SATURATION}."
    )
    print(
        "                   - --enable-luminance + --luminance-tmo=reinhard02: "
        f"post-gamma={DEFAULT_POST_GAMMA}, brightness={DEFAULT_REINHARD02_BRIGHTNESS}, "
        f"contrast={DEFAULT_REINHARD02_CONTRAST}, saturation={DEFAULT_REINHARD02_SATURATION}."
    )
    print(
        "                   - --enable-luminance + other --luminance-tmo: "
        f"post-gamma={DEFAULT_POST_GAMMA}, brightness={DEFAULT_BRIGHTNESS}, "
        f"contrast={DEFAULT_CONTRAST}, saturation={DEFAULT_SATURATION}."
    )
    print("  --luminance-hdr-model=<name>")
    print(f"                   - Luminance HDR model (default: {DEFAULT_LUMINANCE_HDR_MODEL}).")
    print("  --luminance-hdr-weight=<name>")
    print(f"                   - Luminance weighting function (default: {DEFAULT_LUMINANCE_HDR_WEIGHT}).")
    print("  --luminance-hdr-response-curve=<name>")
    print(
        f"                   - Luminance response curve (default: {DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE})."
    )
    print("  --luminance-tmo=<name>")
    print(f"                   - Luminance tone mapper (default: {DEFAULT_LUMINANCE_TMO}).")
    print()
    print("  Luminance operators:")
    operator_rows = _build_two_line_operator_rows(_LUMINANCE_OPERATOR_TABLE_ENTRIES)
    _print_box_table(
        _LUMINANCE_OPERATOR_TABLE_HEADERS,
        operator_rows,
        header_rows=(_LUMINANCE_OPERATOR_TABLE_SECONDARY_HEADER,),
    )
    print()
    print("  Luminance operator main CLI controls:")
    _print_box_table(_LUMINANCE_CONTROL_TABLE_HEADERS, _LUMINANCE_CONTROL_TABLE_ROWS)
    print()
    print("  --tmo* <value> | --tmo*=<value>")
    print("                   - Forward explicit luminance-hdr-cli --tmo* parameters as-is.")
    print("  [platform]       - Command is available on Linux only.")
    print("  --help           - Show this help message.")


def _parse_ev_option(ev_raw):
    """@brief Parse and validate one EV option value.

    @details Converts the raw token to `float` and validates membership against
    the supported EV value set used by bracket multiplier computation.
    @param ev_raw {str} EV token extracted from command arguments.
    @return {float|None} Parsed EV value when valid; `None` otherwise.
    @satisfies REQ-056
    """

    try:
        ev_value = float(ev_raw)
    except ValueError:
        print_error(f"Invalid --ev value: {ev_raw}")
        print_error("Allowed values: 0.5, 1, 1.5, 2")
        return None

    if ev_value not in SUPPORTED_EV_VALUES:
        print_error(f"Unsupported --ev value: {ev_raw}")
        print_error("Allowed values: 0.5, 1, 1.5, 2")
        return None

    return ev_value


def _parse_luminance_text_option(option_name, option_raw):
    """@brief Parse and validate non-empty luminance string option value.

    @details Normalizes surrounding spaces, lowercases token, rejects empty
    values, and rejects ambiguous values that start with option prefix marker.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {str|None} Parsed normalized option token when valid; `None` otherwise.
    @satisfies REQ-061
    """

    option_value = option_raw.strip().lower()
    if not option_value:
        print_error(f"Invalid {option_name} value: empty value")
        return None
    if option_value.startswith("-"):
        print_error(f"Invalid {option_name} value: {option_raw}")
        return None
    return option_value


def _parse_gamma_option(gamma_raw):
    """@brief Parse and validate one gamma option value pair.

    @details Accepts comma-separated positive float pair in `a,b` format with
    optional surrounding parentheses, normalizes to `(a, b)` tuple, and rejects
    malformed, non-numeric, or non-positive values.
    @param gamma_raw {str} Raw gamma token extracted from CLI args.
    @return {tuple[float, float]|None} Parsed gamma tuple when valid; `None` otherwise.
    @satisfies REQ-064
    """

    gamma_text = gamma_raw.strip()
    if gamma_text.startswith("(") and gamma_text.endswith(")"):
        gamma_text = gamma_text[1:-1].strip()

    gamma_parts = [part.strip() for part in gamma_text.split(",")]
    if len(gamma_parts) != 2 or not gamma_parts[0] or not gamma_parts[1]:
        print_error(f"Invalid --gamma value: {gamma_raw}")
        print_error("Expected format: --gamma=<a,b> with positive numeric values.")
        return None

    try:
        gamma_a = float(gamma_parts[0])
        gamma_b = float(gamma_parts[1])
    except ValueError:
        print_error(f"Invalid --gamma value: {gamma_raw}")
        print_error("Expected format: --gamma=<a,b> with positive numeric values.")
        return None

    if gamma_a <= 0.0 or gamma_b <= 0.0:
        print_error(f"Invalid --gamma value: {gamma_raw}")
        print_error("Gamma values must be greater than zero.")
        return None

    return (gamma_a, gamma_b)


def _parse_positive_float_option(option_name, option_raw):
    """@brief Parse and validate one positive float option value.

    @details Converts option token to `float`, requires value greater than zero,
    and emits deterministic parse errors on malformed values.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {float|None} Parsed positive float value when valid; `None` otherwise.
    @satisfies REQ-065
    """

    try:
        option_value = float(option_raw)
    except ValueError:
        print_error(f"Invalid {option_name} value: {option_raw}")
        return None

    if option_value <= 0.0:
        print_error(f"Invalid {option_name} value: {option_raw}")
        print_error(f"{option_name} must be greater than zero.")
        return None
    return option_value


def _parse_tmo_passthrough_value(option_name, option_raw):
    """@brief Parse and validate one luminance `--tmo*` passthrough value.

    @details Rejects empty values and preserves original payload for
    transparent forwarding to `luminance-hdr-cli`.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {str|None} Original value when valid; `None` otherwise.
    @satisfies REQ-067
    """

    if option_raw.strip() == "":
        print_error(f"Invalid {option_name} value: empty value")
        return None
    return option_raw


def _parse_jpg_compression_option(compression_raw):
    """@brief Parse and validate JPEG compression option value.

    @details Converts option token to `int`, requires inclusive range
    `[0, 100]`, and emits deterministic parse errors on malformed values.
    @param compression_raw {str} Raw compression token value from CLI args.
    @return {int|None} Parsed JPEG compression level when valid; `None` otherwise.
    @satisfies REQ-065
    """

    try:
        compression_value = int(compression_raw)
    except ValueError:
        print_error(f"Invalid --jpg-compression value: {compression_raw}")
        return None

    if compression_value < 0 or compression_value > 100:
        print_error(f"Invalid --jpg-compression value: {compression_raw}")
        print_error("Allowed range: 0..100")
        return None
    return compression_value


def _parse_wow_mode_option(wow_raw):
    """@brief Parse wow implementation selector option value.

    @details Accepts case-insensitive wow implementation names and normalizes
    to canonical values for runtime dispatch.
    @param wow_raw {str} Raw wow implementation token.
    @return {str|None} Canonical wow mode (`ImageMagick` or `OpenCV`) or `None` on parse failure.
    @satisfies REQ-065, REQ-073, REQ-075
    """

    wow_text = wow_raw.strip()
    if not wow_text:
        print_error("Invalid --wow value: empty value")
        return None
    wow_text_lower = wow_text.lower()
    if wow_text_lower == "imagemagick":
        return "ImageMagick"
    if wow_text_lower == "opencv":
        return "OpenCV"
    print_error(f"Invalid --wow value: {wow_raw}")
    print_error("Allowed values: ImageMagick, OpenCV")
    return None


def _resolve_default_postprocess(enable_luminance, luminance_tmo):
    """@brief Resolve backend-specific postprocess defaults.

    @details Selects neutral defaults for enfuse and non-`reinhard02` luminance
    operators, and selects tuned defaults for luminance `reinhard02`.
    @param enable_luminance {bool} Backend selector state.
    @param luminance_tmo {str} Selected luminance tone-mapping operator.
    @return {tuple[float, float, float, float]} Defaults in `(post_gamma, brightness, contrast, saturation)` order.
    @satisfies REQ-069, REQ-071, REQ-072
    """

    if not enable_luminance:
        return (
            DEFAULT_POST_GAMMA,
            DEFAULT_BRIGHTNESS,
            DEFAULT_CONTRAST,
            DEFAULT_SATURATION,
        )

    if luminance_tmo == "reinhard02":
        return (
            DEFAULT_POST_GAMMA,
            DEFAULT_REINHARD02_BRIGHTNESS,
            DEFAULT_REINHARD02_CONTRAST,
            DEFAULT_REINHARD02_SATURATION,
        )

    return (
        DEFAULT_POST_GAMMA,
        DEFAULT_BRIGHTNESS,
        DEFAULT_CONTRAST,
        DEFAULT_SATURATION,
    )


def _parse_run_options(args):
    """@brief Parse CLI args into input, output, and EV parameters.

    @details Supports positional file arguments, optional `--ev=<value>` or
    `--ev <value>`, optional `--gamma=<a,b>` or `--gamma <a,b>`, optional
    postprocess controls, required backend selector (`--enable-enfuse` or
    `--enable-luminance`), and luminance backend
    controls including explicit `--tmo*` passthrough options, optional wow
    implementation selector (`--wow <ImageMagick|OpenCV>`); rejects unknown
    options and invalid arity.
    @param args {list[str]} Raw command argument vector.
    @return {tuple[Path, Path, float, tuple[float, float], PostprocessOptions, bool, LuminanceOptions]|None} Parsed `(input, output, ev, gamma, postprocess, enable_luminance, luminance_options)` tuple; `None` on parse failure.
    @satisfies REQ-055, REQ-056, REQ-060, REQ-061, REQ-064, REQ-065, REQ-067, REQ-069, REQ-071, REQ-072, REQ-073, REQ-075
    """

    positional = []
    ev_value = DEFAULT_EV
    gamma_value = DEFAULT_GAMMA
    post_gamma = DEFAULT_POST_GAMMA
    brightness = DEFAULT_BRIGHTNESS
    contrast = DEFAULT_CONTRAST
    saturation = DEFAULT_SATURATION
    jpg_compression = DEFAULT_JPG_COMPRESSION
    post_gamma_set = False
    brightness_set = False
    contrast_set = False
    saturation_set = False
    wow_mode = None
    enable_enfuse = False
    enable_luminance = False
    luminance_hdr_model = DEFAULT_LUMINANCE_HDR_MODEL
    luminance_hdr_weight = DEFAULT_LUMINANCE_HDR_WEIGHT
    luminance_hdr_response_curve = DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE
    luminance_tmo = DEFAULT_LUMINANCE_TMO
    luminance_tmo_extra_args = []
    luminance_option_specified = False
    idx = 0

    while idx < len(args):
        token = args[idx]
        if token == "--enable-enfuse":
            enable_enfuse = True
            idx += 1
            continue

        if token == "--enable-luminance":
            enable_luminance = True
            idx += 1
            continue

        if token == "--wow":
            if idx + 1 >= len(args):
                print_error("Missing value for --wow")
                return None
            if args[idx + 1].startswith("--"):
                print_error("Missing value for --wow")
                return None
            parsed_wow_mode = _parse_wow_mode_option(args[idx + 1])
            if parsed_wow_mode is None:
                return None
            wow_mode = parsed_wow_mode
            idx += 2
            continue

        if token.startswith("--wow="):
            parsed_wow_mode = _parse_wow_mode_option(token.split("=", 1)[1])
            if parsed_wow_mode is None:
                return None
            wow_mode = parsed_wow_mode
            idx += 1
            continue

        if token == "--luminance-hdr-model":
            if idx + 1 >= len(args):
                print_error("Missing value for --luminance-hdr-model")
                return None
            parsed_value = _parse_luminance_text_option("--luminance-hdr-model", args[idx + 1])
            if parsed_value is None:
                return None
            luminance_hdr_model = parsed_value
            luminance_option_specified = True
            idx += 2
            continue

        if token.startswith("--luminance-hdr-model="):
            parsed_value = _parse_luminance_text_option("--luminance-hdr-model", token.split("=", 1)[1])
            if parsed_value is None:
                return None
            luminance_hdr_model = parsed_value
            luminance_option_specified = True
            idx += 1
            continue

        if token == "--luminance-hdr-weight":
            if idx + 1 >= len(args):
                print_error("Missing value for --luminance-hdr-weight")
                return None
            parsed_value = _parse_luminance_text_option("--luminance-hdr-weight", args[idx + 1])
            if parsed_value is None:
                return None
            luminance_hdr_weight = parsed_value
            luminance_option_specified = True
            idx += 2
            continue

        if token.startswith("--luminance-hdr-weight="):
            parsed_value = _parse_luminance_text_option("--luminance-hdr-weight", token.split("=", 1)[1])
            if parsed_value is None:
                return None
            luminance_hdr_weight = parsed_value
            luminance_option_specified = True
            idx += 1
            continue

        if token == "--luminance-hdr-response-curve":
            if idx + 1 >= len(args):
                print_error("Missing value for --luminance-hdr-response-curve")
                return None
            parsed_value = _parse_luminance_text_option("--luminance-hdr-response-curve", args[idx + 1])
            if parsed_value is None:
                return None
            luminance_hdr_response_curve = parsed_value
            luminance_option_specified = True
            idx += 2
            continue

        if token.startswith("--luminance-hdr-response-curve="):
            parsed_value = _parse_luminance_text_option(
                "--luminance-hdr-response-curve", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            luminance_hdr_response_curve = parsed_value
            luminance_option_specified = True
            idx += 1
            continue

        if token == "--luminance-tmo":
            if idx + 1 >= len(args):
                print_error("Missing value for --luminance-tmo")
                return None
            parsed_value = _parse_luminance_text_option("--luminance-tmo", args[idx + 1])
            if parsed_value is None:
                return None
            luminance_tmo = parsed_value
            luminance_option_specified = True
            idx += 2
            continue

        if token.startswith("--luminance-tmo="):
            parsed_value = _parse_luminance_text_option("--luminance-tmo", token.split("=", 1)[1])
            if parsed_value is None:
                return None
            luminance_tmo = parsed_value
            luminance_option_specified = True
            idx += 1
            continue

        if token.startswith("--tmo"):
            if token == "--tmo":
                print_error("Unknown option: --tmo")
                return None

            option_name = token
            option_value = None
            consume_count = 1
            if "=" in token:
                option_name, option_value = token.split("=", 1)
            else:
                if idx + 1 >= len(args):
                    print_error(f"Missing value for {token}")
                    return None
                option_value = args[idx + 1]
                if option_value.startswith("--"):
                    print_error(f"Missing value for {token}")
                    return None
                consume_count = 2

            parsed_value = _parse_tmo_passthrough_value(option_name, option_value)
            if parsed_value is None:
                return None
            luminance_tmo_extra_args.extend((option_name, parsed_value))
            luminance_option_specified = True
            idx += consume_count
            continue

        if token == "--ev":
            if idx + 1 >= len(args):
                print_error("Missing value for --ev")
                return None
            parsed_ev = _parse_ev_option(args[idx + 1])
            if parsed_ev is None:
                return None
            ev_value = parsed_ev
            idx += 2
            continue

        if token.startswith("--ev="):
            parsed_ev = _parse_ev_option(token.split("=", 1)[1])
            if parsed_ev is None:
                return None
            ev_value = parsed_ev
            idx += 1
            continue

        if token == "--gamma":
            if idx + 1 >= len(args):
                print_error("Missing value for --gamma")
                return None
            parsed_gamma = _parse_gamma_option(args[idx + 1])
            if parsed_gamma is None:
                return None
            gamma_value = parsed_gamma
            idx += 2
            continue

        if token.startswith("--gamma="):
            parsed_gamma = _parse_gamma_option(token.split("=", 1)[1])
            if parsed_gamma is None:
                return None
            gamma_value = parsed_gamma
            idx += 1
            continue

        if token == "--post-gamma":
            if idx + 1 >= len(args):
                print_error("Missing value for --post-gamma")
                return None
            parsed_post_gamma = _parse_positive_float_option("--post-gamma", args[idx + 1])
            if parsed_post_gamma is None:
                return None
            post_gamma = parsed_post_gamma
            post_gamma_set = True
            idx += 2
            continue

        if token.startswith("--post-gamma="):
            parsed_post_gamma = _parse_positive_float_option("--post-gamma", token.split("=", 1)[1])
            if parsed_post_gamma is None:
                return None
            post_gamma = parsed_post_gamma
            post_gamma_set = True
            idx += 1
            continue

        if token == "--brightness":
            if idx + 1 >= len(args):
                print_error("Missing value for --brightness")
                return None
            parsed_brightness = _parse_positive_float_option("--brightness", args[idx + 1])
            if parsed_brightness is None:
                return None
            brightness = parsed_brightness
            brightness_set = True
            idx += 2
            continue

        if token.startswith("--brightness="):
            parsed_brightness = _parse_positive_float_option("--brightness", token.split("=", 1)[1])
            if parsed_brightness is None:
                return None
            brightness = parsed_brightness
            brightness_set = True
            idx += 1
            continue

        if token == "--contrast":
            if idx + 1 >= len(args):
                print_error("Missing value for --contrast")
                return None
            parsed_contrast = _parse_positive_float_option("--contrast", args[idx + 1])
            if parsed_contrast is None:
                return None
            contrast = parsed_contrast
            contrast_set = True
            idx += 2
            continue

        if token.startswith("--contrast="):
            parsed_contrast = _parse_positive_float_option("--contrast", token.split("=", 1)[1])
            if parsed_contrast is None:
                return None
            contrast = parsed_contrast
            contrast_set = True
            idx += 1
            continue

        if token == "--saturation":
            if idx + 1 >= len(args):
                print_error("Missing value for --saturation")
                return None
            parsed_saturation = _parse_positive_float_option("--saturation", args[idx + 1])
            if parsed_saturation is None:
                return None
            saturation = parsed_saturation
            saturation_set = True
            idx += 2
            continue

        if token.startswith("--saturation="):
            parsed_saturation = _parse_positive_float_option("--saturation", token.split("=", 1)[1])
            if parsed_saturation is None:
                return None
            saturation = parsed_saturation
            saturation_set = True
            idx += 1
            continue

        if token == "--jpg-compression":
            if idx + 1 >= len(args):
                print_error("Missing value for --jpg-compression")
                return None
            parsed_compression = _parse_jpg_compression_option(args[idx + 1])
            if parsed_compression is None:
                return None
            jpg_compression = parsed_compression
            idx += 2
            continue

        if token.startswith("--jpg-compression="):
            parsed_compression = _parse_jpg_compression_option(token.split("=", 1)[1])
            if parsed_compression is None:
                return None
            jpg_compression = parsed_compression
            idx += 1
            continue

        if token.startswith("-"):
            print_error(f"Unknown option: {token}")
            return None

        positional.append(token)
        idx += 1

    if len(positional) != 2:
        print_error("Usage: dng2hdr2jpg <input.dng> <output.jpg> [--ev=<value>] [--gamma=<a,b>]")
        return None

    if enable_enfuse == enable_luminance:
        print_error("Exactly one backend selector is required: --enable-enfuse or --enable-luminance")
        return None

    if luminance_option_specified and not enable_luminance:
        print_error("Luminance options require --enable-luminance")
        return None

    (
        backend_post_gamma,
        backend_brightness,
        backend_contrast,
        backend_saturation,
    ) = _resolve_default_postprocess(enable_luminance, luminance_tmo)
    if not post_gamma_set:
        post_gamma = backend_post_gamma
    if not brightness_set:
        brightness = backend_brightness
    if not contrast_set:
        contrast = backend_contrast
    if not saturation_set:
        saturation = backend_saturation

    return (
        Path(positional[0]),
        Path(positional[1]),
        ev_value,
        gamma_value,
        PostprocessOptions(
            post_gamma=post_gamma,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            jpg_compression=jpg_compression,
            wow_mode=wow_mode,
        ),
        enable_luminance,
        LuminanceOptions(
            hdr_model=luminance_hdr_model,
            hdr_weight=luminance_hdr_weight,
            hdr_response_curve=luminance_hdr_response_curve,
            tmo=luminance_tmo,
            tmo_extra_args=tuple(luminance_tmo_extra_args),
        ),
    )


def _load_image_dependencies():
    """@brief Load optional Python dependencies required by `dng2hdr2jpg`.

    @details Imports `rawpy` for RAW decoding and `imageio` for image IO using
    `imageio.v3` when available with fallback to top-level `imageio` module.
    @return {tuple[ModuleType, ModuleType, ModuleType, ModuleType]|None} `(rawpy_module, imageio_module, pil_image_module, pil_enhance_module)` on success; `None` on missing dependency.
    @satisfies REQ-059, REQ-066, REQ-074
    """

    try:
        import rawpy  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: rawpy")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow")
        return None

    try:
        import imageio.v3 as imageio  # type: ignore
    except ModuleNotFoundError:
        try:
            import imageio  # type: ignore
        except ModuleNotFoundError:
            print_error("Python dependency missing: imageio")
            print_error("Install dependencies with: uv pip install rawpy imageio pillow")
            return None

    try:
        from PIL import Image as pil_image  # type: ignore
        from PIL import ImageEnhance as pil_enhance  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: pillow")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow")
        return None

    return rawpy, imageio, pil_image, pil_enhance


def _parse_exif_datetime_to_timestamp(datetime_raw):
    """@brief Parse one EXIF datetime token into POSIX timestamp.

    @details Normalizes scalar EXIF datetime input (`str` or `bytes`) and parses
    strict EXIF format `YYYY:MM:DD HH:MM:SS` to generate filesystem timestamp.
    @param datetime_raw {str|bytes|object} EXIF datetime scalar.
    @return {float|None} Parsed POSIX timestamp; `None` when value is missing or invalid.
    @satisfies REQ-074
    """

    if datetime_raw is None:
        return None
    if isinstance(datetime_raw, bytes):
        datetime_text = datetime_raw.decode("utf-8", errors="ignore").strip()
    else:
        datetime_text = str(datetime_raw).strip()
    if not datetime_text:
        return None
    try:
        parsed_datetime = datetime.strptime(datetime_text, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    return parsed_datetime.timestamp()


def _extract_dng_exif_payload_and_timestamp(pil_image_module, input_dng):
    """@brief Extract DNG EXIF payload bytes and preferred datetime timestamp.

    @details Opens input DNG via Pillow, reads EXIF mapping, serializes payload
    for JPEG `exif` save parameter, and resolves filesystem timestamp priority:
    `DateTimeOriginal`(36867) > `DateTimeDigitized`(36868) > `DateTime`(306).
    @param pil_image_module {ModuleType} Imported Pillow Image module.
    @param input_dng {Path} Source DNG path.
    @return {tuple[bytes|None, float|None]} `(exif_payload, exif_timestamp)` with `None` for unavailable components.
    @satisfies REQ-066, REQ-074
    """

    if not hasattr(pil_image_module, "open"):
        return (None, None)
    try:
        with pil_image_module.open(str(input_dng)) as source_image:
            if not hasattr(source_image, "getexif"):
                return (None, None)
            exif_data = source_image.getexif()
            if not exif_data:
                return (None, None)
            exif_payload = exif_data.tobytes() if hasattr(exif_data, "tobytes") else None
            exif_timestamp = None
            for exif_tag in (36867, 36868, 306):
                exif_timestamp = _parse_exif_datetime_to_timestamp(exif_data.get(exif_tag))
                if exif_timestamp is not None:
                    break
            return (exif_payload, exif_timestamp)
    except (OSError, ValueError, TypeError, AttributeError):
        return (None, None)


def _set_output_file_timestamps(output_jpg, exif_timestamp):
    """@brief Set output JPG atime and mtime from EXIF timestamp.

    @details Applies EXIF-derived POSIX timestamp to both access and
    modification times using `os.utime`.
    @param output_jpg {Path} Output JPG path.
    @param exif_timestamp {float} Source EXIF-derived POSIX timestamp.
    @return {None} Side effects only.
    @exception OSError Raised when filesystem metadata update fails.
    @satisfies REQ-074
    """

    os.utime(output_jpg, (exif_timestamp, exif_timestamp))


def _build_exposure_multipliers(ev_value):
    """@brief Compute bracketing brightness multipliers from EV value.

    @details Produces exactly three multipliers mapped to exposure stops
    `[-ev, 0, +ev]` as powers of two for RAW postprocess brightness control.
    @param ev_value {float} Exposure bracket EV delta.
    @return {tuple[float, float, float]} Multipliers in order `(under, base, over)`.
    @satisfies REQ-057
    """

    return (2 ** (-ev_value), 1.0, 2 ** ev_value)


def _write_bracket_images(raw_handle, imageio_module, multipliers, gamma_value, temp_dir):
    """@brief Materialize three bracket TIFF files from one RAW handle.

    @details Invokes `raw.postprocess` with `output_bps=16`,
    `use_camera_wb=True`, `no_auto_bright=True`, and configurable gamma pair
    for deterministic HDR-oriented bracket extraction before merge.
    @param raw_handle {Any} Opened RAW handle from `rawpy.imread`.
    @param imageio_module {ModuleType} Imported imageio module with `imwrite`.
    @param multipliers {tuple[float, float, float]} Ordered exposure multipliers.
    @param gamma_value {tuple[float, float]} Gamma pair forwarded to RAW postprocess.
    @param temp_dir {Path} Directory for intermediate TIFF artifacts.
    @return {list[Path]} Ordered temporary TIFF file paths.
    @satisfies REQ-057
    """

    labels = ("ev_minus", "ev_zero", "ev_plus")
    bracket_paths = []

    for label, multiplier in zip(labels, multipliers):
        temp_path = temp_dir / f"{label}.tif"
        print_info(f"Extracting bracket {label}: brightness={multiplier:.4f}x")
        rgb_data = raw_handle.postprocess(
            bright=multiplier,
            output_bps=16,
            use_camera_wb=True,
            no_auto_bright=True,
            gamma=gamma_value,
        )
        imageio_module.imwrite(str(temp_path), rgb_data)
        bracket_paths.append(temp_path)

    return bracket_paths


def _order_bracket_paths(bracket_paths):
    """@brief Validate and reorder bracket TIFF paths for deterministic backend argv.

    @details Enforces exact exposure order `<ev_minus.tif> <ev_zero.tif> <ev_plus.tif>`
    required by luminance-hdr-cli command generation and raises on missing labels.
    @param bracket_paths {list[Path]} Temporary bracket TIFF paths generated from RAW.
    @return {list[Path]} Reordered bracket path list in deterministic exposure order.
    @exception ValueError Raised when any expected bracket label is missing.
    @satisfies REQ-062
    """

    expected = ("ev_minus.tif", "ev_zero.tif", "ev_plus.tif")
    by_name = {path.name: path for path in bracket_paths}
    ordered = []
    missing = []
    for name in expected:
        path = by_name.get(name)
        if path is None:
            missing.append(name)
            continue
        ordered.append(path)
    if missing:
        raise ValueError(f"Missing expected bracket files: {', '.join(missing)}")
    return ordered


def _run_enfuse(bracket_paths, merged_tiff):
    """@brief Merge bracket TIFF files into one HDR TIFF via `enfuse`.

    @details Builds deterministic enfuse argv with LZW compression and executes
    subprocess in checked mode to propagate command failures.
    @param bracket_paths {list[Path]} Ordered intermediate exposure TIFF paths.
    @param merged_tiff {Path} Output merged TIFF target path.
    @return {None} Side effects only.
    @exception subprocess.CalledProcessError Raised when `enfuse` returns non-zero exit status.
    @satisfies REQ-058
    """

    command = [
        "enfuse",
        f"--output={merged_tiff}",
        "--compression=lzw",
        *[str(path) for path in bracket_paths],
    ]
    subprocess.run(command, check=True)


def _run_luminance_hdr_cli(bracket_paths, output_hdr_tiff, ev_value, luminance_options):
    """@brief Merge bracket TIFF files into one HDR TIFF via `luminance-hdr-cli`.

    @details Builds deterministic luminance-hdr-cli argv using EV sequence,
    HDR model controls, tone-mapper controls, mandatory `--ldrTiff 16b`,
    optional explicit `--tmo*` passthrough arguments, and ordered exposure
    inputs (`ev_minus`, `ev_zero`, `ev_plus`), then writes to TIFF output path
    used by shared postprocess conversion.
    @param bracket_paths {list[Path]} Ordered intermediate exposure TIFF paths.
    @param output_hdr_tiff {Path} Output HDR TIFF target path.
    @param ev_value {float} EV bracket delta used to generate exposure files.
    @param luminance_options {LuminanceOptions} Luminance backend command controls.
    @return {None} Side effects only.
    @exception subprocess.CalledProcessError Raised when `luminance-hdr-cli` returns non-zero exit status.
    @satisfies REQ-060, REQ-061, REQ-062, REQ-067, REQ-068
    """

    ordered_paths = _order_bracket_paths(bracket_paths)
    command = [
        "luminance-hdr-cli",
        "-e",
        f"{-ev_value:g},0,{ev_value:g}",
        "--hdrModel",
        luminance_options.hdr_model,
        "--hdrWeight",
        luminance_options.hdr_weight,
        "--hdrResponseCurve",
        luminance_options.hdr_response_curve,
        "--tmo",
        luminance_options.tmo,
        "--ldrTiff",
        "16b",
        *luminance_options.tmo_extra_args,
        "-o",
        str(output_hdr_tiff),
        *[str(path) for path in ordered_paths],
    ]
    subprocess.run(command, check=True)


def _convert_compression_to_quality(jpg_compression):
    """@brief Convert JPEG compression level to Pillow quality value.

    @details Maps inclusive compression range `[0, 100]` to inclusive quality
    range `[100, 1]` preserving deterministic inverse relation.
    @param jpg_compression {int} JPEG compression level.
    @return {int} Pillow quality value in `[1, 100]`.
    @satisfies REQ-065, REQ-066
    """

    return max(1, min(100, 100 - jpg_compression))


def _resolve_imagemagick_command():
    """@brief Resolve ImageMagick executable name for current runtime.

    @details Probes `magick` first (ImageMagick 7+ preferred CLI), then
    `convert` (legacy-compatible CLI alias) to preserve wow-stage compatibility
    across distributions that package ImageMagick under different executable
    names.
    @return {str|None} Resolved executable token (`magick` or `convert`) or
      `None` when no supported executable is available.
    @satisfies REQ-059, REQ-073
    """

    for executable in ("magick", "convert"):
        if shutil.which(executable) is not None:
            return executable
    return None


def _resolve_wow_opencv_dependencies():
    """@brief Resolve OpenCV wow runtime dependencies.

    @details Imports `cv2` and `numpy` modules required by OpenCV wow pipeline
    execution and returns `None` with deterministic error output when missing.
    @return {tuple[ModuleType, ModuleType]|None} `(cv2_module, numpy_module)` when available; `None` on dependency failure.
    @satisfies REQ-059, REQ-073, REQ-075
    """

    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: opencv-python")
        print_error("Install dependencies with: uv pip install opencv-python numpy")
        return None
    try:
        import numpy as numpy_module  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: numpy")
        print_error("Install dependencies with: uv pip install opencv-python numpy")
        return None
    return (cv2, numpy_module)


def _apply_validated_wow_pipeline(postprocessed_input, wow_output, imagemagick_command):
    """@brief Execute validated wow pipeline over temporary lossless 16-bit TIFF files.

    @details Uses ImageMagick to normalize source data to 16-bit-per-channel TIFF,
    applies deterministic denoise/level/sigmoidal/vibrance/high-pass overlay
    stages, and writes lossless wow output artifact consumed by JPG encoder.
    @param postprocessed_input {Path} Temporary postprocess image input path.
    @param wow_output {Path} Temporary wow output TIFF path.
    @param imagemagick_command {str} Resolved ImageMagick executable token.
    @return {None} Side effects only.
    @exception subprocess.CalledProcessError Raised when ImageMagick returns non-zero.
    @satisfies REQ-073
    """

    wow_input_16 = wow_output.parent / "wow_input_16.tif"
    to_16_bit_command = [
        imagemagick_command,
        str(postprocessed_input),
        "-colorspace",
        "sRGB",
        "-depth",
        "16",
        "-compress",
        "LZW",
        str(wow_input_16),
    ]
    subprocess.run(to_16_bit_command, check=True)

    wow_command = [
        imagemagick_command,
        str(wow_input_16),
        "-depth",
        "16",
        "-selective-blur",
        "0x2+10%",
        "-channel",
        "RGB",
        "-level",
        "0.1%,99.9%",
        "+channel",
        "-sigmoidal-contrast",
        "3x50%",
        "-colorspace",
        "HSL",
        "-channel",
        "G",
        "-gamma",
        "0.8",
        "+channel",
        "-colorspace",
        "sRGB",
        "(",
        "-clone",
        "0",
        "-clone",
        "0",
        "-blur",
        "0x2.5",
        "-compose",
        "mathematics",
        "-define",
        "compose:args=0,1,-1,0.5",
        "-composite",
        "-colorspace",
        "gray",
        ")",
        "-compose",
        "Overlay",
        "-composite",
        "-depth",
        "16",
        "-compress",
        "LZW",
        str(wow_output),
    ]
    subprocess.run(wow_command, check=True)


def _clamp01(np_module, values):
    """@brief Clamp numeric image tensor values into `[0.0, 1.0]` interval.

    @details Applies vectorized clipping to ensure deterministic bounded values
    for OpenCV wow pipeline float-domain operations.
    @param np_module {ModuleType} Imported numpy module.
    @param values {object} Numeric tensor-like payload.
    @return {object} Clipped tensor payload.
    @satisfies REQ-075
    """

    return np_module.clip(values, 0.0, 1.0)


def _gaussian_kernel_2d(np_module, sigma, radius=None):
    """@brief Build normalized 2D Gaussian kernel.

    @details Creates deterministic Gaussian kernel used by selective blur stage;
    returns identity kernel when `sigma <= 0`.
    @param np_module {ModuleType} Imported numpy module.
    @param sigma {float} Gaussian sigma value.
    @param radius {int|None} Optional kernel radius override.
    @return {object} Normalized 2D kernel tensor.
    @satisfies REQ-075
    """

    if sigma <= 0:
        return np_module.array([[1.0]], dtype=np_module.float64)
    if radius is None:
        radius = max(1, int(np_module.ceil(3.0 * sigma)))
    axis = np_module.arange(-radius, radius + 1, dtype=np_module.float64)
    xx, yy = np_module.meshgrid(axis, axis)
    kernel = np_module.exp(-(xx**2 + yy**2) / (2.0 * sigma * sigma))
    kernel /= np_module.sum(kernel)
    return kernel


def _rgb_to_hsl(np_module, rgb):
    """@brief Convert RGB float tensor to HSL channels.

    @details Implements explicit HSL conversion for OpenCV wow saturation-gamma
    stage without delegating to external color-space helpers.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB tensor in `[0.0, 1.0]`.
    @return {tuple[object, object, object]} `(h, s, l)` channel tensors.
    @satisfies REQ-075
    """

    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    cmax = np_module.maximum(np_module.maximum(r, g), b)
    cmin = np_module.minimum(np_module.minimum(r, g), b)
    delta = cmax - cmin
    lightness = 0.5 * (cmax + cmin)
    saturation = np_module.zeros_like(lightness)
    nonzero = delta > 1e-12
    saturation[nonzero] = delta[nonzero] / (1.0 - np_module.abs(2.0 * lightness[nonzero] - 1.0))
    hue = np_module.zeros_like(lightness)
    mask_r = nonzero & (cmax == r)
    mask_g = nonzero & (cmax == g)
    mask_b = nonzero & (cmax == b)
    hue[mask_r] = ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6.0
    hue[mask_g] = ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2.0
    hue[mask_b] = ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4.0
    hue = (hue / 6.0) % 1.0
    return (hue, saturation, lightness)


def _hue_to_rgb(np_module, p_values, q_values, t_values):
    """@brief Convert one hue-shift channel to RGB component.

    @details Evaluates piecewise hue interpolation branch used by HSL-to-RGB
    conversion in OpenCV wow pipeline.
    @param np_module {ModuleType} Imported numpy module.
    @param p_values {object} Lower chroma interpolation boundary.
    @param q_values {object} Upper chroma interpolation boundary.
    @param t_values {object} Hue-shifted channel tensor.
    @return {object} RGB component tensor.
    @satisfies REQ-075
    """

    t_values = t_values % 1.0
    output = np_module.empty_like(t_values)
    case1 = t_values < (1.0 / 6.0)
    case2 = (t_values >= (1.0 / 6.0)) & (t_values < 0.5)
    case3 = (t_values >= 0.5) & (t_values < (2.0 / 3.0))
    case4 = ~(case1 | case2 | case3)
    output[case1] = p_values[case1] + (q_values[case1] - p_values[case1]) * 6.0 * t_values[case1]
    output[case2] = q_values[case2]
    output[case3] = p_values[case3] + (q_values[case3] - p_values[case3]) * ((2.0 / 3.0) - t_values[case3]) * 6.0
    output[case4] = p_values[case4]
    return output


def _hsl_to_rgb(np_module, hue, saturation, lightness):
    """@brief Convert HSL channels to RGB float tensor.

    @details Reconstructs RGB tensor with explicit achromatic/chromatic branches
    for OpenCV wow saturation-gamma stage.
    @param np_module {ModuleType} Imported numpy module.
    @param hue {object} Hue channel tensor.
    @param saturation {object} Saturation channel tensor.
    @param lightness {object} Lightness channel tensor.
    @return {object} RGB tensor in `[0.0, 1.0]`.
    @satisfies REQ-075
    """

    rgb = np_module.zeros(hue.shape + (3,), dtype=np_module.float64)
    achromatic = saturation <= 1e-12
    rgb[achromatic, 0] = lightness[achromatic]
    rgb[achromatic, 1] = lightness[achromatic]
    rgb[achromatic, 2] = lightness[achromatic]
    chromatic = ~achromatic
    if np_module.any(chromatic):
        lightness_chromatic = lightness[chromatic]
        saturation_chromatic = saturation[chromatic]
        hue_chromatic = hue[chromatic]
        q_values = np_module.where(
            lightness_chromatic < 0.5,
            lightness_chromatic * (1.0 + saturation_chromatic),
            lightness_chromatic + saturation_chromatic - lightness_chromatic * saturation_chromatic,
        )
        p_values = 2.0 * lightness_chromatic - q_values
        rgb[chromatic, 0] = _hue_to_rgb(np_module, p_values, q_values, hue_chromatic + 1.0 / 3.0)
        rgb[chromatic, 1] = _hue_to_rgb(np_module, p_values, q_values, hue_chromatic)
        rgb[chromatic, 2] = _hue_to_rgb(np_module, p_values, q_values, hue_chromatic - 1.0 / 3.0)
    return _clamp01(np_module, rgb)


def _selective_blur_contrast_gated_vectorized(np_module, rgb, sigma=2.0, threshold_percent=10.0):
    """@brief Execute contrast-gated selective blur stage.

    @details Applies vectorized contrast-gated neighborhood accumulation over
    Gaussian kernel offsets to emulate selective blur behavior.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param sigma {float} Gaussian sigma.
    @param threshold_percent {float} Luma-difference threshold percent.
    @return {object} Blurred RGB float tensor.
    @satisfies REQ-075
    """

    height, width, _channels = rgb.shape
    kernel = _gaussian_kernel_2d(np_module, sigma=sigma)
    radius = kernel.shape[0] // 2
    threshold = threshold_percent / 100.0
    gray = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    rgb_padded = np_module.pad(rgb, ((radius, radius), (radius, radius), (0, 0)), mode="reflect")
    gray_padded = np_module.pad(gray, ((radius, radius), (radius, radius)), mode="reflect")
    out_numerator = np_module.zeros_like(rgb)
    out_denominator = np_module.zeros_like(gray)
    for delta_y in range(2 * radius + 1):
        for delta_x in range(2 * radius + 1):
            weight = kernel[delta_y, delta_x]
            if weight <= 1e-5:
                continue
            shifted_gray = gray_padded[delta_y:delta_y + height, delta_x:delta_x + width]
            shifted_rgb = rgb_padded[delta_y:delta_y + height, delta_x:delta_x + width, :]
            mask = np_module.abs(shifted_gray - gray) <= threshold
            weighted_mask = mask * weight
            out_denominator += weighted_mask
            out_numerator += shifted_rgb * weighted_mask[..., None]
    valid = out_denominator > 1e-15
    output = np_module.where(valid[..., None], out_numerator / out_denominator[..., None], rgb)
    return _clamp01(np_module, output)


def _level_per_channel_adaptive(np_module, rgb, low_pct=0.1, high_pct=99.9):
    """@brief Execute adaptive per-channel level normalization.

    @details Applies percentile-based level stretching independently for each
    RGB channel.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param low_pct {float} Low percentile threshold.
    @param high_pct {float} High percentile threshold.
    @return {object} Level-normalized RGB float tensor.
    @satisfies REQ-075
    """

    output = np_module.empty_like(rgb)
    for channel_index in range(3):
        channel = rgb[..., channel_index]
        low_value = np_module.percentile(channel, low_pct)
        high_value = np_module.percentile(channel, high_pct)
        scale = 1.0 / max(high_value - low_value, 1e-12)
        output[..., channel_index] = (channel - low_value) * scale
    return _clamp01(np_module, output)


def _sigmoidal_contrast(np_module, rgb, contrast=3.0, midpoint=0.5):
    """@brief Execute sigmoidal contrast stage.

    @details Applies logistic remapping with bounded normalization for each RGB
    channel.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param contrast {float} Logistic slope.
    @param midpoint {float} Logistic midpoint.
    @return {object} Contrast-adjusted RGB float tensor.
    @satisfies REQ-075
    """

    x_values = _clamp01(np_module, rgb)
    def logistic(z_values):
        return 1.0 / (1.0 + np_module.exp(-z_values))
    low_bound = logistic(contrast * (0.0 - midpoint))
    high_bound = logistic(contrast * (1.0 - midpoint))
    mapped = logistic(contrast * (x_values - midpoint))
    mapped = (mapped - low_bound) / max(high_bound - low_bound, 1e-12)
    return _clamp01(np_module, mapped)


def _vibrance_hsl_gamma(np_module, rgb, saturation_gamma=0.8):
    """@brief Execute HSL saturation gamma stage.

    @details Converts RGB to HSL, applies saturation gamma transform, and
    converts back to RGB.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param saturation_gamma {float} Saturation gamma denominator value.
    @return {object} Saturation-adjusted RGB float tensor.
    @satisfies REQ-075
    """

    hue, saturation, lightness = _rgb_to_hsl(np_module, rgb)
    saturation = _clamp01(np_module, saturation) ** (1.0 / saturation_gamma)
    output = _hsl_to_rgb(np_module, hue, saturation, lightness)
    return _clamp01(np_module, output)


def _gaussian_blur_rgb(cv2_module, np_module, rgb, sigma):
    """@brief Execute RGB Gaussian blur with reflected border mode.

    @details Computes odd kernel size from sigma and applies OpenCV Gaussian
    blur preserving reflected border behavior.
    @param cv2_module {ModuleType} Imported cv2 module.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param sigma {float} Gaussian sigma.
    @return {object} Blurred RGB float tensor.
    @satisfies REQ-075
    """

    kernel_size = max(3, int(np_module.ceil(6.0 * sigma)) | 1)
    blurred = cv2_module.GaussianBlur(
        rgb,
        (kernel_size, kernel_size),
        sigmaX=sigma,
        sigmaY=sigma,
        borderType=cv2_module.BORDER_REFLECT,
    )
    return _clamp01(np_module, blurred)


def _high_pass_math_gray(cv2_module, np_module, rgb, blur_sigma=2.5):
    """@brief Execute high-pass math grayscale stage.

    @details Computes high-pass response as `A - B + 0.5` over RGB channels and
    converts to luminance grayscale tensor.
    @param cv2_module {ModuleType} Imported cv2 module.
    @param np_module {ModuleType} Imported numpy module.
    @param rgb {object} RGB float tensor in `[0.0, 1.0]`.
    @param blur_sigma {float} Gaussian blur sigma for high-pass base.
    @return {object} Grayscale float tensor in `[0.0, 1.0]`.
    @satisfies REQ-075
    """

    blurred = _gaussian_blur_rgb(cv2_module, np_module, rgb, sigma=blur_sigma)
    high_pass = rgb - blurred + 0.5
    high_pass = _clamp01(np_module, high_pass)
    gray = 0.2126 * high_pass[..., 0] + 0.7152 * high_pass[..., 1] + 0.0722 * high_pass[..., 2]
    return _clamp01(np_module, gray)


def _overlay_composite(np_module, base_rgb, overlay_gray):
    """@brief Execute overlay composite stage.

    @details Applies conditional overlay blend equation over RGB base and
    grayscale overlay tensors.
    @param np_module {ModuleType} Imported numpy module.
    @param base_rgb {object} Base RGB float tensor in `[0.0, 1.0]`.
    @param overlay_gray {object} Overlay grayscale tensor in `[0.0, 1.0]`.
    @return {object} Overlay-composited RGB float tensor.
    @satisfies REQ-075
    """

    source = np_module.repeat(overlay_gray[..., None], 3, axis=2)
    destination = base_rgb
    output = np_module.where(
        destination <= 0.5,
        2.0 * source * destination,
        1.0 - 2.0 * (1.0 - source) * (1.0 - destination),
    )
    return _clamp01(np_module, output)


def _apply_validated_wow_pipeline_opencv(input_file, output_file, cv2_module, np_module):
    """@brief Execute validated wow pipeline using OpenCV and numpy.

    @details Reads 16-bit RGB image, performs explicit 16-bit-to-float
    normalization, executes selective blur, adaptive levels, sigmoidal
    contrast, HSL saturation gamma, high-pass/overlay stages, then restores
    float payload to 16-bit-per-channel RGB TIFF output.
    @param input_file {Path} Source TIFF path.
    @param output_file {Path} Output TIFF path.
    @param cv2_module {ModuleType} Imported cv2 module.
    @param np_module {ModuleType} Imported numpy module.
    @return {None} Side effects only.
    @exception OSError Raised when source file is missing.
    @exception RuntimeError Raised when OpenCV read/write fails.
    @satisfies REQ-073, REQ-075
    """

    if not input_file.exists():
        raise OSError(f"OpenCV wow input file not found: {input_file}")
    image_bgr = cv2_module.imread(str(input_file), cv2_module.IMREAD_UNCHANGED)
    if image_bgr is None:
        raise RuntimeError(f"OpenCV failed to read wow input: {input_file}")
    if len(image_bgr.shape) != 3 or image_bgr.shape[2] != 3:
        raise RuntimeError(f"OpenCV wow input must be 3-channel image: {input_file}")
    if str(getattr(image_bgr, "dtype", "")) != "uint16":
        raise RuntimeError(f"OpenCV wow input must be uint16 image: {input_file}")
    rgb_float = cv2_module.cvtColor(image_bgr, cv2_module.COLOR_BGR2RGB).astype(np_module.float64) / 65535.0
    rgb_float = _selective_blur_contrast_gated_vectorized(np_module, rgb_float, sigma=2.0, threshold_percent=10.0)
    rgb_float = _level_per_channel_adaptive(np_module, rgb_float, low_pct=0.1, high_pct=99.9)
    rgb_float = _sigmoidal_contrast(np_module, rgb_float, contrast=3.0, midpoint=0.5)
    rgb_float = _vibrance_hsl_gamma(np_module, rgb_float, saturation_gamma=0.8)
    high_pass_gray = _high_pass_math_gray(cv2_module, np_module, rgb_float, blur_sigma=2.5)
    rgb_float = _overlay_composite(np_module, rgb_float, high_pass_gray)
    output_rgb_u16 = np_module.clip(np_module.round(rgb_float * 65535.0), 0, 65535).astype(np_module.uint16)
    output_bgr_u16 = cv2_module.cvtColor(output_rgb_u16, cv2_module.COLOR_RGB2BGR)
    if not cv2_module.imwrite(str(output_file), output_bgr_u16):
        raise RuntimeError(f"OpenCV failed to write wow output: {output_file}")


def _encode_jpg(
    imageio_module,
    pil_image_module,
    pil_enhance_module,
    merged_tiff,
    output_jpg,
    postprocess_options,
    imagemagick_command=None,
    wow_opencv_dependencies=None,
    source_exif_payload=None,
):
    """@brief Encode merged HDR TIFF payload into final JPG output.

    @details Loads merged image payload, down-converts to `uint8` when source
    dynamic range exceeds JPEG-native depth, applies shared gamma/brightness/
    contrast/saturation postprocessing, optionally executes wow stage over
    temporary lossless 16-bit TIFF intermediates, and writes JPEG with
    configured compression level for both HDR backends.
    @param imageio_module {ModuleType} Imported imageio module with `imread` and `imwrite`.
    @param pil_image_module {ModuleType} Imported Pillow image module.
    @param pil_enhance_module {ModuleType} Imported Pillow ImageEnhance module.
    @param merged_tiff {Path} Merged TIFF source path produced by `enfuse`.
    @param output_jpg {Path} Final JPG output path.
    @param postprocess_options {PostprocessOptions} Shared TIFF-to-JPG correction settings.
    @param imagemagick_command {str|None} Optional pre-resolved ImageMagick executable.
    @param wow_opencv_dependencies {tuple[ModuleType, ModuleType]|None} Optional `(cv2, numpy)` modules for OpenCV wow implementation.
    @param source_exif_payload {bytes|None} Serialized EXIF payload copied from input DNG.
    @return {None} Side effects only.
    @exception RuntimeError Raised when wow mode dependencies are missing or wow mode value is unsupported.
    @satisfies REQ-058, REQ-066, REQ-069, REQ-073, REQ-074, REQ-075
    """

    merged_data = imageio_module.imread(str(merged_tiff))
    dtype_name = str(getattr(merged_data, "dtype", ""))
    if dtype_name and dtype_name != "uint8":
        scaled = merged_data / 257.0
        if hasattr(scaled, "clip"):
            scaled = scaled.clip(0, 255)
        if hasattr(scaled, "astype"):
            merged_data = scaled.astype("uint8")
        else:
            merged_data = scaled

    if hasattr(merged_data, "save") and hasattr(merged_data, "convert"):
        pil_image = merged_data
    else:
        pil_image = pil_image_module.fromarray(merged_data)

    if getattr(pil_image, "mode", "") == "RGBA":
        pil_image = pil_image.convert("RGB")

    if postprocess_options.post_gamma != 1.0:
        lut = [
            max(
                0,
                min(
                    255,
                    int(round(((value / 255.0) ** (1.0 / postprocess_options.post_gamma)) * 255.0)),
                ),
            )
            for value in range(256)
        ]
        band_count = len(getattr(pil_image, "getbands", lambda: ("R", "G", "B"))())
        pil_image = pil_image.point(lut * max(1, band_count))

    if postprocess_options.brightness != 1.0:
        pil_image = pil_enhance_module.Brightness(pil_image).enhance(postprocess_options.brightness)
    if postprocess_options.contrast != 1.0:
        pil_image = pil_enhance_module.Contrast(pil_image).enhance(postprocess_options.contrast)
    if postprocess_options.saturation != 1.0:
        pil_image = pil_enhance_module.Color(pil_image).enhance(postprocess_options.saturation)

    if postprocess_options.wow_mode is not None:
        with tempfile.TemporaryDirectory(prefix="dng2hdr2jpg-wow-") as wow_temp_dir_raw:
            wow_temp_dir = Path(wow_temp_dir_raw)
            postprocessed_input = wow_temp_dir / "postprocessed_input.tif"
            wow_output = wow_temp_dir / "wow_output.tif"
            pil_image.save(str(postprocessed_input), format="TIFF", compression="tiff_lzw")
            if postprocess_options.wow_mode == "ImageMagick":
                if imagemagick_command is None:
                    imagemagick_command = _resolve_imagemagick_command()
                if imagemagick_command is None:
                    raise RuntimeError("Missing required dependency: ImageMagick executable (magick or convert)")
                _apply_validated_wow_pipeline(
                    postprocessed_input=postprocessed_input,
                    wow_output=wow_output,
                    imagemagick_command=imagemagick_command,
                )
            elif postprocess_options.wow_mode == "OpenCV":
                if wow_opencv_dependencies is None:
                    raise RuntimeError("Missing required dependencies: opencv-python and numpy")
                cv2_module, np_module = wow_opencv_dependencies
                _apply_validated_wow_pipeline_opencv(
                    input_file=postprocessed_input,
                    output_file=wow_output,
                    cv2_module=cv2_module,
                    np_module=np_module,
                )
            else:
                raise RuntimeError(f"Unsupported wow mode: {postprocess_options.wow_mode}")
            wow_data = imageio_module.imread(str(wow_output))
            wow_dtype_name = str(getattr(wow_data, "dtype", ""))
            if wow_dtype_name and wow_dtype_name != "uint8":
                wow_scaled = wow_data / 257.0
                if hasattr(wow_scaled, "clip"):
                    wow_scaled = wow_scaled.clip(0, 255)
                if hasattr(wow_scaled, "astype"):
                    wow_data = wow_scaled.astype("uint8")
                else:
                    wow_data = wow_scaled
            if hasattr(wow_data, "save") and hasattr(wow_data, "convert"):
                pil_image = wow_data
            else:
                pil_image = pil_image_module.fromarray(wow_data)

    if getattr(pil_image, "mode", "") != "RGB":
        pil_image = pil_image.convert("RGB")

    save_kwargs = {
        "format": "JPEG",
        "quality": _convert_compression_to_quality(postprocess_options.jpg_compression),
        "optimize": True,
    }
    if source_exif_payload is not None:
        save_kwargs["exif"] = source_exif_payload
    pil_image.save(str(output_jpg), **save_kwargs)


def _collect_processing_errors(rawpy_module):
    """@brief Build deterministic tuple of recoverable processing exceptions.

    @details Combines common IO/value/subprocess errors with rawpy-specific
    decoding error classes when present in runtime module version.
    @param rawpy_module {ModuleType} Imported rawpy module.
    @return {tuple[type[BaseException], ...]} Ordered deduplicated exception class tuple.
    @satisfies REQ-059
    """

    classes = [OSError, ValueError, RuntimeError, subprocess.CalledProcessError]
    for class_name in (
        "LibRawError",
        "LibRawFileUnsupportedError",
        "LibRawIOError",
        "LibRawFatalError",
        "LibRawNonFatalError",
    ):
        candidate = getattr(rawpy_module, class_name, None)
        if isinstance(candidate, type):
            classes.append(candidate)

    deduplicated = []
    for class_type in classes:
        if class_type not in deduplicated:
            deduplicated.append(class_type)
    return tuple(deduplicated)


def _is_supported_runtime_os():
    """@brief Validate runtime platform support for `dng2hdr2jpg`.

    @details Accepts Linux runtime only; emits explicit non-Linux unsupported
    message that includes OS label (`Windows` or `MacOS`) for deterministic UX.
    @return {bool} `True` when runtime OS is Linux; `False` otherwise.
    @satisfies REQ-055, REQ-059
    """

    runtime_os = get_runtime_os()
    if runtime_os == "linux":
        return True

    runtime_label = _RUNTIME_OS_LABELS.get(runtime_os, runtime_os)
    print_error(
        f"dng2hdr2jpg is not available on {runtime_label}; this command is Linux-only."
    )
    return False


def run(args):
    """@brief Execute `dng2hdr2jpg` command pipeline.

    @details Parses command options, validates dependencies, extracts three RAW
    brackets, executes selected `enfuse` flow or selected luminance-hdr-cli flow,
    writes JPG output, and guarantees temporary artifact cleanup through isolated
    temporary directory lifecycle.
    @param args {list[str]} Command argument vector excluding command token.
    @return {int} `0` on success; `1` on parse/validation/dependency/processing failure.
    @satisfies REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075
    """

    if not _is_supported_runtime_os():
        return 1

    parsed = _parse_run_options(args)
    if parsed is None:
        return 1

    (
        input_dng,
        output_jpg,
        ev_value,
        gamma_value,
        postprocess_options,
        enable_luminance,
        luminance_options,
    ) = parsed

    if input_dng.suffix.lower() != ".dng":
        print_error(f"Input file must have .dng extension: {input_dng}")
        return 1

    if not input_dng.exists() or not input_dng.is_file():
        print_error(f"Input DNG file not found: {input_dng}")
        return 1

    output_parent = output_jpg.parent
    if output_parent and not output_parent.exists():
        print_error(f"Output directory does not exist: {output_parent}")
        return 1

    if enable_luminance:
        if shutil.which("luminance-hdr-cli") is None:
            print_error("Missing required dependency: luminance-hdr-cli")
            return 1
    else:
        if shutil.which("enfuse") is None:
            print_error("Missing required dependency: enfuse")
            return 1
    imagemagick_command = None
    wow_opencv_dependencies = None
    if postprocess_options.wow_mode == "ImageMagick":
        imagemagick_command = _resolve_imagemagick_command()
        if imagemagick_command is None:
            print_error("Missing required dependency: ImageMagick executable (magick or convert)")
            return 1
    elif postprocess_options.wow_mode == "OpenCV":
        wow_opencv_dependencies = _resolve_wow_opencv_dependencies()
        if wow_opencv_dependencies is None:
            return 1

    dependencies = _load_image_dependencies()
    if dependencies is None:
        return 1

    rawpy_module, imageio_module, pil_image_module, pil_enhance_module = dependencies
    source_exif_payload, source_exif_timestamp = _extract_dng_exif_payload_and_timestamp(
        pil_image_module=pil_image_module,
        input_dng=input_dng,
    )
    processing_errors = _collect_processing_errors(rawpy_module)
    multipliers = _build_exposure_multipliers(ev_value)

    print_info(f"Reading DNG input: {input_dng}")
    print_info(f"Using EV bracket: {ev_value}")
    print_info(f"Using gamma pair: {gamma_value[0]:g},{gamma_value[1]:g}")
    print_info(
        "Postprocess factors: "
        f"gamma={postprocess_options.post_gamma:g}, "
        f"brightness={postprocess_options.brightness:g}, "
        f"contrast={postprocess_options.contrast:g}, "
        f"saturation={postprocess_options.saturation:g}, "
        f"jpg-compression={postprocess_options.jpg_compression}, "
        f"wow={postprocess_options.wow_mode or 'disabled'}"
    )
    if enable_luminance:
        extra_args_text = ""
        if luminance_options.tmo_extra_args:
            extra_args_text = f", tmoExtraArgs=[{' '.join(luminance_options.tmo_extra_args)}]"
        print_info(
            "HDR backend: luminance-hdr-cli "
            f"(hdrModel={luminance_options.hdr_model}, "
            f"hdrWeight={luminance_options.hdr_weight}, "
            f"hdrResponseCurve={luminance_options.hdr_response_curve}, "
            f"tmo={luminance_options.tmo}{extra_args_text})"
        )
    else:
        print_info("HDR backend: enfuse")

    with tempfile.TemporaryDirectory(prefix="dng2hdr2jpg-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        merged_tiff = temp_dir / "merged_hdr.tif"

        try:
            with rawpy_module.imread(str(input_dng)) as raw_handle:
                bracket_paths = _write_bracket_images(
                    raw_handle=raw_handle,
                    imageio_module=imageio_module,
                    multipliers=multipliers,
                    gamma_value=gamma_value,
                    temp_dir=temp_dir,
                )
            if enable_luminance:
                _run_luminance_hdr_cli(
                    bracket_paths=bracket_paths,
                    output_hdr_tiff=merged_tiff,
                    ev_value=ev_value,
                    luminance_options=luminance_options,
                )
            else:
                _run_enfuse(bracket_paths=bracket_paths, merged_tiff=merged_tiff)
            _encode_jpg(
                imageio_module=imageio_module,
                pil_image_module=pil_image_module,
                pil_enhance_module=pil_enhance_module,
                merged_tiff=merged_tiff,
                output_jpg=output_jpg,
                postprocess_options=postprocess_options,
                imagemagick_command=imagemagick_command,
                wow_opencv_dependencies=wow_opencv_dependencies,
                source_exif_payload=source_exif_payload,
            )
            if source_exif_timestamp is not None:
                _set_output_file_timestamps(output_jpg=output_jpg, exif_timestamp=source_exif_timestamp)
        except processing_errors as error:
            print_error(f"dng2hdr2jpg processing failed: {error}")
            return 1

    print_success(f"HDR JPG created: {output_jpg}")
    return 0
