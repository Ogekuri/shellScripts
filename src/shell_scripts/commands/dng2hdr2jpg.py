#!/usr/bin/env python3
"""@brief Convert one DNG file into one HDR-merged JPG output.

@details Implements bracketed RAW extraction with three synthetic exposures
(`-ev`, `0`, `+ev`), merges them through selected `enfuse` or selected
`luminance-hdr-cli` flow with deterministic HDR model parameters, applies
in-memory 16-bit postprocess, optionally executes in-memory 16-bit
`magic_retouch`, then writes final JPG to user-selected output path.
Temporary artifacts are isolated in a temporary directory and removed
automatically on success and failure.
@satisfies PRJ-003, DES-008, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075, REQ-076, REQ-077
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
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
DEFAULT_MAGIC_COLOR_BALANCE_STRENGTH = 0.18
DEFAULT_MAGIC_DENOISE_SIGMA_COLOR = 0.06
DEFAULT_MAGIC_DENOISE_SIGMA_SPACE = 4.0
DEFAULT_MAGIC_MICROCONTRAST_RADIUS = 10
DEFAULT_MAGIC_MICROCONTRAST_EPS = 1e-3
DEFAULT_MAGIC_MICROCONTRAST_AMOUNT = 0.14
DEFAULT_MAGIC_VIBRANCE_STRENGTH = 0.09
DEFAULT_MAGIC_SHARPEN_SIGMA = 1.0
DEFAULT_MAGIC_SHARPEN_AMOUNT = 0.28
DEFAULT_MAGIC_PROTECT_BLEND = 0.85
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
    @return {None} Immutable dataclass container.
    @satisfies REQ-065, REQ-066, REQ-069, REQ-071, REQ-072
    """

    post_gamma: float
    brightness: float
    contrast: float
    saturation: float
    jpg_compression: int


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


@dataclass(frozen=True)
class MagicRetouchOptions:
    """@brief Hold deterministic `magic_retouch` option values.

    @details Encapsulates all configurable parameters for the in-memory 16-bit
    magic-retouch pipeline activated by `--magic-retouch`.
    @param enabled {bool} Pipeline enable flag.
    @param color_balance_strength {float} LAB color-balance correction factor.
    @param denoise_sigma_color {float} Bilateral denoise color sigma in normalized domain.
    @param denoise_sigma_space {float} Bilateral denoise spatial sigma.
    @param microcontrast_radius {int} Box-filter window radius for guided micro-contrast.
    @param microcontrast_eps {float} Guided filter regularization epsilon.
    @param microcontrast_amount {float} Guided-detail amplification factor.
    @param vibrance_strength {float} Saturation gain for low-saturation pixels.
    @param sharpen_sigma {float} Gaussian sigma for luminance unsharp mask.
    @param sharpen_amount {float} Luminance unsharp blend amount.
    @param protect_blend {float} Extremes-protection blend factor in `[0, 1]`.
    @return {None} Immutable dataclass container.
    @satisfies REQ-073, REQ-075
    """

    enabled: bool
    color_balance_strength: float
    denoise_sigma_color: float
    denoise_sigma_space: float
    microcontrast_radius: int
    microcontrast_eps: float
    microcontrast_amount: float
    vibrance_strength: float
    sharpen_sigma: float
    sharpen_amount: float
    protect_blend: float


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
    controls, shared postprocessing controls, backend selection, optional
    `magic_retouch` controls, and luminance-hdr-cli tone-mapping options.
    @param version {str} CLI version label to append in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-063, REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-075
    """

    print(
        f"Usage: {PROGRAM} dng2hdr2jpg <input.dng> <output.jpg> "
        f"[--ev=<value>] [--gamma=<a,b>] [--post-gamma=<value>] "
        f"[--brightness=<value>] [--contrast=<value>] [--saturation=<value>] "
        f"[--jpg-compression=<0..100>] (--enable-enfuse | --enable-luminance) "
        f"[--magic-retouch] [--magic-color-balance-strength=<0..1>] "
        f"[--magic-denoise-sigma-color=<value>] [--magic-denoise-sigma-space=<value>] "
        f"[--magic-microcontrast-radius=<value>] [--magic-microcontrast-eps=<value>] "
        f"[--magic-microcontrast-amount=<value>] [--magic-vibrance-strength=<value>] "
        f"[--magic-sharpen-sigma=<value>] [--magic-sharpen-amount=<value>] "
        f"[--magic-protect-blend=<0..1>] "
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
    print("  --magic-retouch            - Enable in-memory 16-bit magic-retouch stage.")
    print(
        "  --magic-color-balance-strength=<0..1>"
        f" - LAB chroma color-balance strength (default: {DEFAULT_MAGIC_COLOR_BALANCE_STRENGTH})."
    )
    print(
        "  --magic-denoise-sigma-color=<value>"
        f" - Bilateral denoise color sigma (default: {DEFAULT_MAGIC_DENOISE_SIGMA_COLOR})."
    )
    print(
        "  --magic-denoise-sigma-space=<value>"
        f" - Bilateral denoise spatial sigma (default: {DEFAULT_MAGIC_DENOISE_SIGMA_SPACE})."
    )
    print(
        "  --magic-microcontrast-radius=<value>"
        f" - Guided filter radius (default: {DEFAULT_MAGIC_MICROCONTRAST_RADIUS})."
    )
    print(
        "  --magic-microcontrast-eps=<value>"
        f" - Guided filter epsilon (default: {DEFAULT_MAGIC_MICROCONTRAST_EPS})."
    )
    print(
        "  --magic-microcontrast-amount=<value>"
        f" - Micro-contrast boost factor (default: {DEFAULT_MAGIC_MICROCONTRAST_AMOUNT})."
    )
    print(
        "  --magic-vibrance-strength=<value>"
        f" - Vibrance gain for low saturation pixels (default: {DEFAULT_MAGIC_VIBRANCE_STRENGTH})."
    )
    print(
        "  --magic-sharpen-sigma=<value>"
        f" - Luma sharpen Gaussian sigma (default: {DEFAULT_MAGIC_SHARPEN_SIGMA})."
    )
    print(
        "  --magic-sharpen-amount=<value>"
        f" - Luma sharpen amount (default: {DEFAULT_MAGIC_SHARPEN_AMOUNT})."
    )
    print(
        "  --magic-protect-blend=<0..1>"
        f" - Extremes-protection blend factor (default: {DEFAULT_MAGIC_PROTECT_BLEND})."
    )
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


def _parse_non_negative_float_option(option_name, option_raw):
    """@brief Parse and validate one non-negative float option value.

    @details Converts option token to `float`, requires value greater than or
    equal to zero, and emits deterministic parse errors on malformed values.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {float|None} Parsed non-negative float value when valid; `None` otherwise.
    @satisfies REQ-073
    """

    try:
        option_value = float(option_raw)
    except ValueError:
        print_error(f"Invalid {option_name} value: {option_raw}")
        return None

    if option_value < 0.0:
        print_error(f"Invalid {option_name} value: {option_raw}")
        print_error(f"{option_name} must be greater than or equal to zero.")
        return None
    return option_value


def _parse_unit_float_option(option_name, option_raw):
    """@brief Parse and validate one unit-interval float option value.

    @details Converts option token to `float`, requires inclusive range
    `[0.0, 1.0]`, and emits deterministic parse errors on malformed values.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {float|None} Parsed unit-interval float value when valid; `None` otherwise.
    @satisfies REQ-073
    """

    try:
        option_value = float(option_raw)
    except ValueError:
        print_error(f"Invalid {option_name} value: {option_raw}")
        return None

    if option_value < 0.0 or option_value > 1.0:
        print_error(f"Invalid {option_name} value: {option_raw}")
        print_error(f"{option_name} must be in range [0.0, 1.0].")
        return None
    return option_value


def _parse_positive_int_option(option_name, option_raw):
    """@brief Parse and validate one positive integer option value.

    @details Converts option token to `int`, requires value greater than zero,
    and emits deterministic parse errors on malformed values.
    @param option_name {str} Long-option identifier used in error messages.
    @param option_raw {str} Raw option token value from CLI args.
    @return {int|None} Parsed positive integer value when valid; `None` otherwise.
    @satisfies REQ-073
    """

    try:
        option_value = int(option_raw)
    except ValueError:
        print_error(f"Invalid {option_name} value: {option_raw}")
        return None

    if option_value <= 0:
        print_error(f"Invalid {option_name} value: {option_raw}")
        print_error(f"{option_name} must be greater than zero.")
        return None
    return option_value


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
    controls including explicit `--tmo*` passthrough options; rejects unknown
    options and invalid arity.
    @param args {list[str]} Raw command argument vector.
    @return {tuple[Path, Path, float, tuple[float, float], PostprocessOptions, bool, LuminanceOptions, MagicRetouchOptions]|None} Parsed `(input, output, ev, gamma, postprocess, enable_luminance, luminance_options, magic_retouch_options)` tuple; `None` on parse failure.
    @satisfies REQ-055, REQ-056, REQ-060, REQ-061, REQ-064, REQ-065, REQ-067, REQ-069, REQ-071, REQ-072, REQ-073
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
    enable_enfuse = False
    enable_luminance = False
    luminance_hdr_model = DEFAULT_LUMINANCE_HDR_MODEL
    luminance_hdr_weight = DEFAULT_LUMINANCE_HDR_WEIGHT
    luminance_hdr_response_curve = DEFAULT_LUMINANCE_HDR_RESPONSE_CURVE
    luminance_tmo = DEFAULT_LUMINANCE_TMO
    luminance_tmo_extra_args = []
    luminance_option_specified = False
    magic_retouch_enabled = False
    magic_color_balance_strength = DEFAULT_MAGIC_COLOR_BALANCE_STRENGTH
    magic_denoise_sigma_color = DEFAULT_MAGIC_DENOISE_SIGMA_COLOR
    magic_denoise_sigma_space = DEFAULT_MAGIC_DENOISE_SIGMA_SPACE
    magic_microcontrast_radius = DEFAULT_MAGIC_MICROCONTRAST_RADIUS
    magic_microcontrast_eps = DEFAULT_MAGIC_MICROCONTRAST_EPS
    magic_microcontrast_amount = DEFAULT_MAGIC_MICROCONTRAST_AMOUNT
    magic_vibrance_strength = DEFAULT_MAGIC_VIBRANCE_STRENGTH
    magic_sharpen_sigma = DEFAULT_MAGIC_SHARPEN_SIGMA
    magic_sharpen_amount = DEFAULT_MAGIC_SHARPEN_AMOUNT
    magic_protect_blend = DEFAULT_MAGIC_PROTECT_BLEND
    idx = 0

    while idx < len(args):
        token = args[idx]
        if token == "--magic-retouch":
            magic_retouch_enabled = True
            idx += 1
            continue

        if token == "--magic-color-balance-strength":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-color-balance-strength")
                return None
            parsed_value = _parse_unit_float_option("--magic-color-balance-strength", args[idx + 1])
            if parsed_value is None:
                return None
            magic_color_balance_strength = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-color-balance-strength="):
            parsed_value = _parse_unit_float_option(
                "--magic-color-balance-strength", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_color_balance_strength = parsed_value
            idx += 1
            continue

        if token == "--magic-denoise-sigma-color":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-denoise-sigma-color")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-denoise-sigma-color", args[idx + 1])
            if parsed_value is None:
                return None
            magic_denoise_sigma_color = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-denoise-sigma-color="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-denoise-sigma-color", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_denoise_sigma_color = parsed_value
            idx += 1
            continue

        if token == "--magic-denoise-sigma-space":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-denoise-sigma-space")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-denoise-sigma-space", args[idx + 1])
            if parsed_value is None:
                return None
            magic_denoise_sigma_space = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-denoise-sigma-space="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-denoise-sigma-space", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_denoise_sigma_space = parsed_value
            idx += 1
            continue

        if token == "--magic-microcontrast-radius":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-microcontrast-radius")
                return None
            parsed_value = _parse_positive_int_option("--magic-microcontrast-radius", args[idx + 1])
            if parsed_value is None:
                return None
            magic_microcontrast_radius = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-microcontrast-radius="):
            parsed_value = _parse_positive_int_option(
                "--magic-microcontrast-radius", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_microcontrast_radius = parsed_value
            idx += 1
            continue

        if token == "--magic-microcontrast-eps":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-microcontrast-eps")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-microcontrast-eps", args[idx + 1])
            if parsed_value is None:
                return None
            magic_microcontrast_eps = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-microcontrast-eps="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-microcontrast-eps", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_microcontrast_eps = parsed_value
            idx += 1
            continue

        if token == "--magic-microcontrast-amount":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-microcontrast-amount")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-microcontrast-amount", args[idx + 1])
            if parsed_value is None:
                return None
            magic_microcontrast_amount = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-microcontrast-amount="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-microcontrast-amount", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_microcontrast_amount = parsed_value
            idx += 1
            continue

        if token == "--magic-vibrance-strength":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-vibrance-strength")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-vibrance-strength", args[idx + 1])
            if parsed_value is None:
                return None
            magic_vibrance_strength = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-vibrance-strength="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-vibrance-strength", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_vibrance_strength = parsed_value
            idx += 1
            continue

        if token == "--magic-sharpen-sigma":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-sharpen-sigma")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-sharpen-sigma", args[idx + 1])
            if parsed_value is None:
                return None
            magic_sharpen_sigma = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-sharpen-sigma="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-sharpen-sigma", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_sharpen_sigma = parsed_value
            idx += 1
            continue

        if token == "--magic-sharpen-amount":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-sharpen-amount")
                return None
            parsed_value = _parse_non_negative_float_option("--magic-sharpen-amount", args[idx + 1])
            if parsed_value is None:
                return None
            magic_sharpen_amount = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-sharpen-amount="):
            parsed_value = _parse_non_negative_float_option(
                "--magic-sharpen-amount", token.split("=", 1)[1]
            )
            if parsed_value is None:
                return None
            magic_sharpen_amount = parsed_value
            idx += 1
            continue

        if token == "--magic-protect-blend":
            if idx + 1 >= len(args):
                print_error("Missing value for --magic-protect-blend")
                return None
            parsed_value = _parse_unit_float_option("--magic-protect-blend", args[idx + 1])
            if parsed_value is None:
                return None
            magic_protect_blend = parsed_value
            idx += 2
            continue

        if token.startswith("--magic-protect-blend="):
            parsed_value = _parse_unit_float_option("--magic-protect-blend", token.split("=", 1)[1])
            if parsed_value is None:
                return None
            magic_protect_blend = parsed_value
            idx += 1
            continue
        if token == "--enable-enfuse":
            enable_enfuse = True
            idx += 1
            continue

        if token == "--enable-luminance":
            enable_luminance = True
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
        ),
        enable_luminance,
        LuminanceOptions(
            hdr_model=luminance_hdr_model,
            hdr_weight=luminance_hdr_weight,
            hdr_response_curve=luminance_hdr_response_curve,
            tmo=luminance_tmo,
            tmo_extra_args=tuple(luminance_tmo_extra_args),
        ),
        MagicRetouchOptions(
            enabled=magic_retouch_enabled,
            color_balance_strength=magic_color_balance_strength,
            denoise_sigma_color=magic_denoise_sigma_color,
            denoise_sigma_space=magic_denoise_sigma_space,
            microcontrast_radius=magic_microcontrast_radius,
            microcontrast_eps=magic_microcontrast_eps,
            microcontrast_amount=magic_microcontrast_amount,
            vibrance_strength=magic_vibrance_strength,
            sharpen_sigma=magic_sharpen_sigma,
            sharpen_amount=magic_sharpen_amount,
            protect_blend=magic_protect_blend,
        ),
    )


def _load_image_dependencies():
    """@brief Load optional Python dependencies required by `dng2hdr2jpg`.

    @details Imports `rawpy` for RAW decoding and `imageio` for image IO using
    `imageio.v3` when available with fallback to top-level `imageio` module.
    @return {tuple[ModuleType, ModuleType, ModuleType, ModuleType, ModuleType, ModuleType]|None} `(rawpy_module, imageio_module, pil_image_module, pil_enhance_module, cv2_module, np_module)` on success; `None` on missing dependency.
    @satisfies REQ-059, REQ-066, REQ-077
    """

    try:
        import rawpy  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: rawpy")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow opencv-python numpy")
        return None

    try:
        import imageio.v3 as imageio  # type: ignore
    except ModuleNotFoundError:
        try:
            import imageio  # type: ignore
        except ModuleNotFoundError:
            print_error("Python dependency missing: imageio")
            print_error("Install dependencies with: uv pip install rawpy imageio pillow opencv-python numpy")
            return None

    try:
        from PIL import Image as pil_image  # type: ignore
        from PIL import ImageEnhance as pil_enhance  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: pillow")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow opencv-python numpy")
        return None

    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: opencv-python")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow opencv-python numpy")
        return None

    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: numpy")
        print_error("Install dependencies with: uv pip install rawpy imageio pillow opencv-python numpy")
        return None

    return rawpy, imageio, pil_image, pil_enhance, cv2, np


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


def _to_float01_from_u16(np_module, image_u16):
    """@brief Convert one uint16 image payload to normalized float image.

    @details Casts uint16 image payload to float32 and normalizes pixel domain
    from `[0, 65535]` to `[0.0, 1.0]`.
    @param np_module {ModuleType} Imported numpy module.
    @param image_u16 {np.ndarray} 16-bit image payload.
    @return {np.ndarray} Float32 normalized image payload.
    @satisfies REQ-066, REQ-076
    """

    return image_u16.astype(np_module.float32) / 65535.0


def _to_u16_from_float01(np_module, image_float):
    """@brief Convert one normalized float image payload to uint16 image.

    @details Clips pixel domain to `[0.0, 1.0]`, scales to `[0, 65535]`, and
    casts to uint16 to preserve 16-bit-per-channel lossless stage continuity.
    @param np_module {ModuleType} Imported numpy module.
    @param image_float {np.ndarray} Float image payload in normalized domain.
    @return {np.ndarray} Uint16 image payload.
    @satisfies REQ-066, REQ-076
    """

    clipped = np_module.clip(image_float, 0.0, 1.0)
    return np_module.rint(clipped * 65535.0).astype(np_module.uint16)


def _apply_postprocess_16bit(np_module, cv2_module, image_u16, postprocess_options):
    """@brief Apply gamma/brightness/contrast/saturation in-memory on uint16 image.

    @details Executes all postprocess controls on normalized float payload and
    converts back to uint16 without lossy 8-bit conversion.
    @param np_module {ModuleType} Imported numpy module.
    @param cv2_module {ModuleType} Imported OpenCV module.
    @param image_u16 {np.ndarray} Input uint16 image payload.
    @param postprocess_options {PostprocessOptions} Postprocess option values.
    @return {np.ndarray} Postprocessed uint16 image payload.
    @satisfies REQ-066, REQ-076
    """

    image_float = _to_float01_from_u16(np_module, image_u16)
    if postprocess_options.post_gamma != 1.0:
        gamma_power = 1.0 / postprocess_options.post_gamma
        image_float = np_module.power(np_module.maximum(image_float, 0.0), gamma_power)

    if postprocess_options.brightness != 1.0:
        image_float = image_float * postprocess_options.brightness
        image_float = np_module.clip(image_float, 0.0, 1.0)

    if postprocess_options.contrast != 1.0:
        image_float = ((image_float - 0.5) * postprocess_options.contrast) + 0.5
        image_float = np_module.clip(image_float, 0.0, 1.0)

    if postprocess_options.saturation != 1.0:
        hsv = cv2_module.cvtColor(image_float, cv2_module.COLOR_RGB2HSV)
        hsv[:, :, 1] = np_module.clip(hsv[:, :, 1] * postprocess_options.saturation, 0.0, 1.0)
        image_float = cv2_module.cvtColor(hsv, cv2_module.COLOR_HSV2RGB)

    return _to_u16_from_float01(np_module, image_float)


def _guided_filter(np_module, cv2_module, guide, src, radius, eps):
    """@brief Apply mono-channel guided filter for edge-aware smoothing.

    @details Builds local mean statistics via box-filter and computes guided
    linear coefficients for deterministic edge-aware base extraction.
    @param np_module {ModuleType} Imported numpy module.
    @param cv2_module {ModuleType} Imported OpenCV module.
    @param guide {np.ndarray} Guide mono channel in `[0, 1]`.
    @param src {np.ndarray} Source mono channel in `[0, 1]`.
    @param radius {int} Box-filter radius.
    @param eps {float} Regularization epsilon.
    @return {np.ndarray} Filtered mono channel in `[0, 1]`.
    @satisfies REQ-075
    """

    ksize = (2 * radius + 1, 2 * radius + 1)
    mean_i = cv2_module.boxFilter(guide, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    mean_p = cv2_module.boxFilter(src, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    mean_ip = cv2_module.boxFilter(guide * src, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    cov_ip = mean_ip - mean_i * mean_p
    mean_ii = cv2_module.boxFilter(guide * guide, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    var_i = mean_ii - mean_i * mean_i
    a = cov_ip / (var_i + eps)
    b = mean_p - a * mean_i
    mean_a = cv2_module.boxFilter(a, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    mean_b = cv2_module.boxFilter(b, ddepth=-1, ksize=ksize, normalize=True, borderType=cv2_module.BORDER_REFLECT)
    return np_module.clip((mean_a * guide) + mean_b, 0.0, 1.0)


def _magic_retouch(np_module, cv2_module, image_u16, magic_options):
    """@brief Execute in-memory 16-bit deterministic magic-retouch pipeline.

    @details Applies mild color balance, light denoise, edge-aware
    micro-contrast, mild vibrance, luminance-only sharpen, and extremes
    protection on normalized float data, then returns uint16 payload.
    @param np_module {ModuleType} Imported numpy module.
    @param cv2_module {ModuleType} Imported OpenCV module.
    @param image_u16 {np.ndarray} Input uint16 image payload.
    @param magic_options {MagicRetouchOptions} Magic-retouch option values.
    @return {np.ndarray} Magic-retouched uint16 image payload.
    @satisfies REQ-074, REQ-075, REQ-076
    """

    original = _to_float01_from_u16(np_module, image_u16)
    out = original.copy()

    # 1) Mild color balance in LAB chroma channels.
    # OpenCV LAB float conversion uses L in [0, 100] and a/b around 0 with range near [-127, 127].
    out_lab = cv2_module.cvtColor(out, cv2_module.COLOR_RGB2LAB)
    channel_l, channel_a, channel_b = cv2_module.split(out_lab)
    a_mean = float(np_module.mean(channel_a))
    b_mean = float(np_module.mean(channel_b))
    channel_a = channel_a - (a_mean * magic_options.color_balance_strength)
    channel_b = channel_b - (b_mean * magic_options.color_balance_strength)
    channel_l = np_module.clip(channel_l, 0.0, 100.0)
    channel_a = np_module.clip(channel_a, -127.0, 127.0)
    channel_b = np_module.clip(channel_b, -127.0, 127.0)
    out = cv2_module.cvtColor(cv2_module.merge([channel_l, channel_a, channel_b]), cv2_module.COLOR_LAB2RGB)

    # 2) Very light denoise.
    denoise_d = 5
    out = cv2_module.bilateralFilter(
        out.astype(np_module.float32),
        d=denoise_d,
        sigmaColor=max(1e-6, magic_options.denoise_sigma_color),
        sigmaSpace=max(1e-6, magic_options.denoise_sigma_space),
        borderType=cv2_module.BORDER_REFLECT,
    )
    out = np_module.clip(out, 0.0, 1.0)

    # 3) Edge-aware micro-contrast on luminance.
    out_lab = cv2_module.cvtColor(out, cv2_module.COLOR_RGB2LAB)
    channel_l, channel_a, channel_b = cv2_module.split(out_lab)
    channel_l_norm = np_module.clip(channel_l / 100.0, 0.0, 1.0)
    gray = cv2_module.cvtColor(out, cv2_module.COLOR_RGB2GRAY)
    base = _guided_filter(
        np_module=np_module,
        cv2_module=cv2_module,
        guide=gray,
        src=channel_l_norm,
        radius=magic_options.microcontrast_radius,
        eps=magic_options.microcontrast_eps,
    )
    detail = channel_l_norm - base
    channel_l_norm = np_module.clip(base + ((1.0 + magic_options.microcontrast_amount) * detail), 0.0, 1.0)
    channel_l = np_module.clip(channel_l_norm * 100.0, 0.0, 100.0)
    out = cv2_module.cvtColor(cv2_module.merge([channel_l, channel_a, channel_b]), cv2_module.COLOR_LAB2RGB)

    # 4) Mild vibrance.
    out_hsv = cv2_module.cvtColor(out, cv2_module.COLOR_RGB2HSV)
    channel_h, channel_s, channel_v = cv2_module.split(out_hsv)
    channel_s = np_module.clip(channel_s, 0.0, 1.0)
    gain = 1.0 + (magic_options.vibrance_strength * (1.0 - channel_s))
    channel_s = np_module.clip(channel_s * gain, 0.0, 1.0)
    out = cv2_module.cvtColor(cv2_module.merge([channel_h, channel_s, channel_v]), cv2_module.COLOR_HSV2RGB)

    # 5) Luminance-only sharpen.
    out_lab = cv2_module.cvtColor(out, cv2_module.COLOR_RGB2LAB)
    channel_l, channel_a, channel_b = cv2_module.split(out_lab)
    blur_l = cv2_module.GaussianBlur(
        channel_l,
        (0, 0),
        sigmaX=magic_options.sharpen_sigma,
        sigmaY=magic_options.sharpen_sigma,
    )
    channel_l = np_module.clip(
        cv2_module.addWeighted(
            channel_l,
            1.0 + magic_options.sharpen_amount,
            blur_l,
            -magic_options.sharpen_amount,
            0.0,
        ),
        0.0,
        100.0,
    )
    out = cv2_module.cvtColor(cv2_module.merge([channel_l, channel_a, channel_b]), cv2_module.COLOR_LAB2RGB)

    # 6) Extremes protection blend.
    gray_original = cv2_module.cvtColor(original, cv2_module.COLOR_RGB2GRAY)
    protection = np_module.clip(np_module.abs(gray_original - 0.5) * 2.0, 0.0, 1.0)
    alpha = 1.0 - ((1.0 - magic_options.protect_blend) * protection)
    out = (alpha[:, :, None] * out) + ((1.0 - alpha[:, :, None]) * original)

    return _to_u16_from_float01(np_module, out)


def _encode_jpg(pil_image_module, image_u16, output_jpg, jpg_compression):
    """@brief Encode one in-memory 16-bit image payload into final JPG output.

    @details Converts in-memory uint16 payload to uint8 for JPEG-compatible
    encoding, normalizes channel-mode to RGB, and writes JPG with configured
    compression level.
    @param pil_image_module {ModuleType} Imported Pillow image module.
    @param image_u16 {np.ndarray} Input uint16 image payload.
    @param output_jpg {Path} Final JPG output path.
    @param jpg_compression {int} JPEG compression level.
    @return {None} Side effects only.
    @satisfies REQ-058, REQ-066, REQ-074, REQ-076
    """

    scaled = image_u16 / 257.0
    if hasattr(scaled, "clip"):
        scaled = scaled.clip(0, 255)
    if hasattr(scaled, "astype"):
        image_u8 = scaled.astype("uint8")
    else:
        image_u8 = scaled
    pil_image = pil_image_module.fromarray(image_u8)

    if getattr(pil_image, "mode", "") == "RGBA":
        pil_image = pil_image.convert("RGB")

    if getattr(pil_image, "mode", "") != "RGB":
        pil_image = pil_image.convert("RGB")

    pil_image.save(
        str(output_jpg),
        format="JPEG",
        quality=_convert_compression_to_quality(jpg_compression),
        optimize=True,
    )


def _read_u16_image(imageio_module, np_module, merged_tiff):
    """@brief Read merged TIFF and normalize payload to uint16 RGB image.

    @details Reads merged TIFF payload, strips alpha channel when present, and
    converts integer payloads to uint16 domain required by in-memory postprocess.
    @param imageio_module {ModuleType} Imported imageio module.
    @param np_module {ModuleType} Imported numpy module.
    @param merged_tiff {Path} Merged HDR TIFF path.
    @return {np.ndarray} Normalized uint16 RGB image payload.
    @satisfies REQ-066, REQ-074, REQ-076
    """

    merged_data = imageio_module.imread(str(merged_tiff))
    image_array = np_module.asarray(merged_data)
    if image_array.ndim == 2:
        image_array = np_module.stack([image_array, image_array, image_array], axis=-1)
    if image_array.ndim == 3 and image_array.shape[2] > 3:
        image_array = image_array[:, :, :3]
    if image_array.dtype == np_module.uint16:
        return image_array
    if np_module.issubdtype(image_array.dtype, np_module.integer):
        max_value = int(np_module.iinfo(image_array.dtype).max)
        if max_value <= 255:
            return (image_array.astype(np_module.uint16) * 257).astype(np_module.uint16)
        scale = 65535.0 / max(1.0, float(max_value))
        return np_module.clip(image_array.astype(np_module.float32) * scale, 0.0, 65535.0).astype(np_module.uint16)
    image_float = np_module.asarray(image_array, dtype=np_module.float32)
    if float(np_module.max(image_float)) <= 1.0:
        image_float = image_float * 65535.0
    return np_module.clip(image_float, 0.0, 65535.0).astype(np_module.uint16)


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
    applies in-memory uint16 postprocess controls, optionally applies in-memory
    uint16 `magic_retouch`, writes JPG output, and guarantees temporary artifact
    cleanup through isolated temporary directory lifecycle.
    @param args {list[str]} Command argument vector excluding command token.
    @return {int} `0` on success; `1` on parse/validation/dependency/processing failure.
    @satisfies REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075, REQ-076, REQ-077
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
        magic_retouch_options,
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

    dependencies = _load_image_dependencies()
    if dependencies is None:
        return 1

    rawpy_module, imageio_module, pil_image_module, _, cv2_module, np_module = dependencies
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
        f"jpg-compression={postprocess_options.jpg_compression}"
    )
    print_info(
        "Magic retouch: "
        + ("enabled" if magic_retouch_options.enabled else "disabled")
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
            image_u16 = _read_u16_image(
                imageio_module=imageio_module,
                np_module=np_module,
                merged_tiff=merged_tiff,
            )
            image_u16 = _apply_postprocess_16bit(
                np_module=np_module,
                cv2_module=cv2_module,
                image_u16=image_u16,
                postprocess_options=postprocess_options,
            )
            if magic_retouch_options.enabled:
                image_u16 = _magic_retouch(
                    np_module=np_module,
                    cv2_module=cv2_module,
                    image_u16=image_u16,
                    magic_options=magic_retouch_options,
                )
            _encode_jpg(
                pil_image_module=pil_image_module,
                image_u16=image_u16,
                output_jpg=output_jpg,
                jpg_compression=postprocess_options.jpg_compression,
            )
        except processing_errors as error:
            print_error(f"dng2hdr2jpg processing failed: {error}")
            return 1

    print_success(f"HDR JPG created: {output_jpg}")
    return 0
