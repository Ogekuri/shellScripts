#!/usr/bin/env python3
"""@brief Convert one DNG file into one HDR-merged JPG output.

@details Implements bracketed RAW extraction with three synthetic exposures
(`-ev`, `0`, `+ev`), merges them through default `enfuse` flow or optional
`luminance-hdr-cli` flow, then writes final JPG to user-selected output path.
Temporary artifacts are isolated in a temporary directory and removed
automatically on success and failure.
@satisfies PRJ-003, DES-008, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063
"""

import shutil
import subprocess
import tempfile
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
DEFAULT_LUMINANCE_OPERATOR = "mantiuk06"
SUPPORTED_EV_VALUES = (0.5, 1.0, 1.5, 2.0)
LUMINANCE_MAP_ALIASES = {
    "ashikhmin": "ashikhmin02",
    "drago": "drago03",
    "durand": "durand02",
    "fattal": "fattal",
    "ferradans": "ferradans11",
    "ferwerda": "ferwerda96",
    "kimkautz": "kimkautz08",
    "lischinski": "lischinski06",
    "mantiuk": "mantiuk06",
    "mantiuk08": "mantiuk08",
    "pattanaik": "pattanaik00",
    "reinhard": "reinhard02",
    "reinhard05": "reinhard05",
    "vanhateren": "vanhateren06",
}
_RUNTIME_OS_LABELS = {
    "windows": "Windows",
    "darwin": "MacOS",
}


def print_help(version):
    """@brief Print help text for the `dng2hdr2jpg` command.

    @details Documents required positional arguments, optional EV control,
    backend selection, and luminance-hdr-cli tone-mapping options.
    @param version {str} CLI version label to append in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-063
    """

    print(
        f"Usage: {PROGRAM} dng2hdr2jpg <input.dng> <output.jpg> "
        f"[--ev=<value>] [--enable-luminance] "
        f"[--luminance-operator=<name>] [--luminance-map-<name>] ({version})"
    )
    print()
    print("dng2hdr2jpg options:")
    print("  <input.dng>      - Input DNG file (required).")
    print("  <output.jpg>     - Output JPG file (required).")
    print("  --ev=<value>     - Exposure bracket EV: 0.5 | 1 | 1.5 | 2 (default: 2).")
    print("  --enable-luminance")
    print("                   - Enable luminance-hdr-cli backend (default backend: enfuse).")
    print("                     Uses alignment engine MTB and applies selected tone mapper.")
    print("  --luminance-operator=<name>")
    print(f"                   - Select luminance-hdr-cli tone mapper (default: {DEFAULT_LUMINANCE_OPERATOR}).")
    print("  --luminance-map-<name>")
    print("                   - Shortcut aliases for common operators:")
    for alias_name, operator_name in LUMINANCE_MAP_ALIASES.items():
        print(f"                     --luminance-map-{alias_name:<10} -> {operator_name}")
    print("                   - Generic form accepts any installed operator name.")
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


def _parse_luminance_operator(operator_raw):
    """@brief Parse and validate one luminance-hdr operator value.

    @details Normalizes surrounding spaces and rejects empty operator values
    required by luminance-hdr-cli `-a` argument generation.
    @param operator_raw {str} Raw luminance operator token from CLI args.
    @return {str|None} Normalized operator string; `None` when invalid.
    @satisfies REQ-061
    """

    operator_value = operator_raw.strip().lower()
    if not operator_value:
        print_error("Invalid luminance operator: empty value")
        return None
    if operator_value.startswith("-"):
        print_error(f"Invalid luminance operator: {operator_raw}")
        return None
    return operator_value


def _parse_luminance_map_flag(map_flag):
    """@brief Parse `--luminance-map-<name>` shortcut option.

    @details Supports explicit aliases and pass-through operator names so every
    installed luminance-hdr-cli operator remains reachable from CLI args.
    @param map_flag {str} CLI token that starts with `--luminance-map-`.
    @return {str|None} Resolved operator name for luminance-hdr-cli; `None` when malformed.
    @satisfies REQ-061, REQ-063
    """

    map_name = map_flag[len("--luminance-map-") :].strip().lower()
    if not map_name:
        print_error("Malformed luminance map option: missing map name")
        return None
    return LUMINANCE_MAP_ALIASES.get(map_name, map_name)


def _parse_run_options(args):
    """@brief Parse CLI args into input, output, and EV parameters.

    @details Supports positional file arguments, optional `--ev=<value>` or
    `--ev <value>`, optional `--enable-luminance`, and luminance operator
    selectors; rejects unknown options and invalid arity.
    @param args {list[str]} Raw command argument vector.
    @return {tuple[Path, Path, float, bool, str]|None} Parsed `(input, output, ev, enable_luminance, luminance_operator)` tuple; `None` on parse failure.
    @satisfies REQ-055, REQ-056, REQ-060, REQ-061
    """

    positional = []
    ev_value = DEFAULT_EV
    enable_luminance = False
    luminance_operator = DEFAULT_LUMINANCE_OPERATOR
    luminance_option_specified = False
    idx = 0

    while idx < len(args):
        token = args[idx]
        if token == "--enable-luminance":
            enable_luminance = True
            idx += 1
            continue

        if token == "--luminance-operator":
            if idx + 1 >= len(args):
                print_error("Missing value for --luminance-operator")
                return None
            parsed_operator = _parse_luminance_operator(args[idx + 1])
            if parsed_operator is None:
                return None
            luminance_operator = parsed_operator
            luminance_option_specified = True
            idx += 2
            continue

        if token.startswith("--luminance-operator="):
            parsed_operator = _parse_luminance_operator(token.split("=", 1)[1])
            if parsed_operator is None:
                return None
            luminance_operator = parsed_operator
            luminance_option_specified = True
            idx += 1
            continue

        if token.startswith("--luminance-map-"):
            parsed_operator = _parse_luminance_map_flag(token)
            if parsed_operator is None:
                return None
            luminance_operator = parsed_operator
            luminance_option_specified = True
            idx += 1
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

        if token.startswith("-"):
            print_error(f"Unknown option: {token}")
            return None

        positional.append(token)
        idx += 1

    if len(positional) != 2:
        print_error("Usage: dng2hdr2jpg <input.dng> <output.jpg> [--ev=<value>]")
        return None

    if luminance_option_specified and not enable_luminance:
        print_error("Luminance operator options require --enable-luminance")
        return None

    return (
        Path(positional[0]),
        Path(positional[1]),
        ev_value,
        enable_luminance,
        luminance_operator,
    )


def _load_image_dependencies():
    """@brief Load optional Python dependencies required by `dng2hdr2jpg`.

    @details Imports `rawpy` for RAW decoding and `imageio` for image IO using
    `imageio.v3` when available with fallback to top-level `imageio` module.
    @return {tuple[ModuleType, ModuleType]|None} `(rawpy_module, imageio_module)` on success; `None` on missing dependency.
    @satisfies REQ-059
    """

    try:
        import rawpy  # type: ignore
    except ModuleNotFoundError:
        print_error("Python dependency missing: rawpy")
        print_error("Install dependencies with: uv pip install rawpy imageio")
        return None

    try:
        import imageio.v3 as imageio  # type: ignore
    except ModuleNotFoundError:
        try:
            import imageio  # type: ignore
        except ModuleNotFoundError:
            print_error("Python dependency missing: imageio")
            print_error("Install dependencies with: uv pip install rawpy imageio")
            return None

    return rawpy, imageio


def _build_exposure_multipliers(ev_value):
    """@brief Compute bracketing brightness multipliers from EV value.

    @details Produces exactly three multipliers mapped to exposure stops
    `[-ev, 0, +ev]` as powers of two for RAW postprocess brightness control.
    @param ev_value {float} Exposure bracket EV delta.
    @return {tuple[float, float, float]} Multipliers in order `(under, base, over)`.
    @satisfies REQ-057
    """

    return (2 ** (-ev_value), 1.0, 2 ** ev_value)


def _write_bracket_images(raw_handle, imageio_module, multipliers, temp_dir):
    """@brief Materialize three bracket TIFF files from one RAW handle.

    @details Invokes `raw.postprocess` with `output_bps=16`,
    `use_camera_wb=True`, and `no_auto_bright=False` for camera white-balance
    aware bracket extraction before HDR merge.
    @param raw_handle {Any} Opened RAW handle from `rawpy.imread`.
    @param imageio_module {ModuleType} Imported imageio module with `imwrite`.
    @param multipliers {tuple[float, float, float]} Ordered exposure multipliers.
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
            no_auto_bright=False,
        )
        imageio_module.imwrite(str(temp_path), rgb_data)
        bracket_paths.append(temp_path)

    return bracket_paths


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


def _run_luminance_hdr_cli(bracket_paths, output_jpg, luminance_operator, ev_value):
    """@brief Merge bracket TIFF files into final JPG via `luminance-hdr-cli`.

    @details Builds deterministic luminance-hdr-cli argv using alignment engine
    `-a MTB`, tone mapper `--tmo <operator>`, and writes directly to requested
    JPG output path.
    @param bracket_paths {list[Path]} Ordered intermediate exposure TIFF paths.
    @param output_jpg {Path} Final JPG output target path.
    @param luminance_operator {str} Selected luminance-hdr-cli tone-mapping operator.
    @param ev_value {float} EV bracket delta used to generate exposure files.
    @return {None} Side effects only.
    @exception subprocess.CalledProcessError Raised when `luminance-hdr-cli` returns non-zero exit status.
    @satisfies REQ-060, REQ-061, REQ-062
    """

    command = [
        "luminance-hdr-cli",
        "-a",
        "MTB",
        "--tmo",
        luminance_operator,
        "-e",
        f"{-ev_value:g},0,{ev_value:g}",
        "-o",
        str(output_jpg),
        *[str(path) for path in bracket_paths],
    ]
    subprocess.run(command, check=True)


def _encode_jpg(imageio_module, merged_tiff, output_jpg):
    """@brief Encode merged HDR TIFF payload into final JPG output.

    @details Loads merged image payload, down-converts to `uint8` when source
    dynamic range exceeds JPEG-native depth, and strips alpha channel payload
    (`RGBA` -> `RGB`) before JPEG write for both Pillow-mode and array payloads.
    @param imageio_module {ModuleType} Imported imageio module with `imread` and `imwrite`.
    @param merged_tiff {Path} Merged TIFF source path produced by `enfuse`.
    @param output_jpg {Path} Final JPG output path.
    @return {None} Side effects only.
    @satisfies REQ-058
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

    mode = getattr(merged_data, "mode", "")
    if mode == "RGBA" and hasattr(merged_data, "convert"):
        merged_data = merged_data.convert("RGB")
    else:
        shape = getattr(merged_data, "shape", ())
        if len(shape) >= 3 and shape[-1] == 4:
            merged_data = merged_data[..., :3]

    imageio_module.imwrite(str(output_jpg), merged_data)


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
    brackets, executes default `enfuse` flow or optional luminance-hdr-cli flow,
    writes JPG output, and guarantees temporary artifact cleanup through isolated
    temporary directory lifecycle.
    @param args {list[str]} Command argument vector excluding command token.
    @return {int} `0` on success; `1` on parse/validation/dependency/processing failure.
    @satisfies REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062
    """

    if not _is_supported_runtime_os():
        return 1

    parsed = _parse_run_options(args)
    if parsed is None:
        return 1

    input_dng, output_jpg, ev_value, enable_luminance, luminance_operator = parsed

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

    rawpy_module, imageio_module = dependencies
    processing_errors = _collect_processing_errors(rawpy_module)
    multipliers = _build_exposure_multipliers(ev_value)

    print_info(f"Reading DNG input: {input_dng}")
    print_info(f"Using EV bracket: {ev_value}")
    if enable_luminance:
        print_info(f"HDR backend: luminance-hdr-cli (operator={luminance_operator})")
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
                    temp_dir=temp_dir,
                )
            if enable_luminance:
                _run_luminance_hdr_cli(
                    bracket_paths=bracket_paths,
                    output_jpg=output_jpg,
                    luminance_operator=luminance_operator,
                    ev_value=ev_value,
                )
            else:
                _run_enfuse(bracket_paths=bracket_paths, merged_tiff=merged_tiff)
                _encode_jpg(
                    imageio_module=imageio_module,
                    merged_tiff=merged_tiff,
                    output_jpg=output_jpg,
                )
        except processing_errors as error:
            print_error(f"dng2hdr2jpg processing failed: {error}")
            return 1

    print_success(f"HDR JPG created: {output_jpg}")
    return 0
