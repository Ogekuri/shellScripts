#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import time
from typing import NoReturn

from shell_scripts.utils import (
    require_commands,
    color_enabled,
    RESET,
    BOLD,
    BRIGHT_RED,
    BRIGHT_GREEN,
    BRIGHT_YELLOW,
    BRIGHT_CYAN,
    BRIGHT_WHITE,
    WHITE,
    c,
)

PROGRAM = "shellscripts"
DESCRIPTION = "Crop PDF pages using Ghostscript with auto or manual bounding box."

LABEL_WIDTH = 19
TERM_COLS = 80


def _init_ui():
    global TERM_COLS
    try:
        TERM_COLS = os.get_terminal_size().columns
    except OSError:
        TERM_COLS = 80
    TERM_COLS = max(60, min(120, TERM_COLS))


def _use_unicode():
    lang = os.environ.get(
        "LC_ALL", os.environ.get("LC_CTYPE", os.environ.get("LANG", ""))
    )
    return "UTF-8" in lang.upper() or "utf8" in lang.lower() or "utf-8" in lang.lower()


def _icons():
    if _use_unicode():
        return {
            "thick": "\u2550",
            "thin": "\u2500",
            "section": "\u25b6",
            "done": "\u2714",
            "warn": "\u26a0",
            "bbox": "\u25fc",
        }
    return {
        "thick": "=",
        "thin": "-",
        "section": ">",
        "done": "OK",
        "warn": "!!",
        "bbox": "#",
    }


def print_help(version):
    print(f"Usage: {PROGRAM} pdf-crop [options] ({version})")
    print()
    print("pdf-crop options:")
    print("  --in <file>              - Input PDF file (required).")
    print("  --out <file>             - Output PDF file (default: crop-<input>).")
    print('  --bbox "L B R T"         - Manual bounding box in PDF points.')
    print('  --margins "L T R B"      - Margin adjustments in PDF points.')
    print("  --analyze-pages <range>  - Pages to use for bbox estimation.")
    print("  --pages <range>          - Page range to export (N, N-, -N, N-M).")
    print("  --help                   - Show this help message.")


def _fmt(n):
    return f"{float(n):.2f}"


def _fmt_quad(a, b, cc, d):
    return f"{_fmt(a)}  {_fmt(b)}  {_fmt(cc)}  {_fmt(d)}"


def _fmt_size(w, h):
    return f"{_fmt(w)} x {_fmt(h)} pt"


def _fmt_bbox_line(left, bottom, right, top):
    return f"L={_fmt(left)}  B={_fmt(bottom)}  R={_fmt(right)}  T={_fmt(top)}"


def _hr(char):
    width = max(50, TERM_COLS - 2)
    print(c(char * width, BRIGHT_WHITE))


def _section(title):
    icons = _icons()
    _hr(icons["thick"])
    print(c(f"{icons['section']} {title}", BRIGHT_YELLOW + BOLD))
    _hr(icons["thin"])


def _kv(key, value):
    if color_enabled():
        print(
            f"  {BRIGHT_CYAN}{BOLD}{key:<{LABEL_WIDTH}}{RESET} {BRIGHT_WHITE}{BOLD}:{RESET} {value}"
        )
    else:
        print(f"  {key:<{LABEL_WIDTH}} : {value}")


def _die(msg) -> NoReturn:
    print(c(f"Error: {msg}", BRIGHT_RED + BOLD), file=sys.stderr)
    sys.exit(1)


def _warn(msg):
    icons = _icons()
    print(c(f"{icons['warn']} {msg}", BRIGHT_YELLOW + BOLD), file=sys.stderr)


def _parse_page_range(spec, max_pages, opt_name):
    if not spec:
        _die(f"{opt_name} requires a value")

    start = 0
    end = 0
    match = re.fullmatch(r"(\d+)", spec)
    if match:
        start = int(match.group(1))
        end = start
    else:
        match = re.fullmatch(r"(\d+)-", spec)
        if match:
            start = int(match.group(1))
            end = max_pages
        else:
            match = re.fullmatch(r"-(\d+)", spec)
            if match:
                start = 1
                end = int(match.group(1))
            else:
                match = re.fullmatch(r"(\d+)-(\d+)", spec)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2))
                else:
                    _die(f"{opt_name} must be: N, N-, -N, or N-M")

    if start < 1:
        _die(f"{opt_name} start must be >= 1")
    if end < start:
        _die(f"{opt_name} invalid: end < start")
    if start > max_pages:
        _die(f"{opt_name} starts beyond document pages ({max_pages})")
    if end > max_pages:
        _die(f"{opt_name} ends beyond document pages ({max_pages})")

    return start, end


def _get_page_count(pdf):
    r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    return None


def _get_mediabox(pdf, page=1):
    r = subprocess.run(
        ["pdfinfo", "-f", str(page), "-l", str(page), "-box", pdf],
        capture_output=True,
        text=True,
    )
    for line in r.stdout.splitlines():
        if "MediaBox:" in line:
            parts = line.split()
            return tuple(float(x) for x in parts[-4:])
    return None


def _compute_auto_bbox(pdf, first_page, last_page):
    r = subprocess.run(
        [
            "gs",
            "-dSAFER",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=bbox",
            f"-dFirstPage={first_page}",
            f"-dLastPage={last_page}",
            "-f",
            pdf,
        ],
        capture_output=True,
        text=True,
    )
    output = r.stderr + "\n" + r.stdout
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    found = False
    for line in output.splitlines():
        if line.startswith("%%HiResBoundingBox:"):
            parts = line.split()
            llx, lly, urx, ury = (
                float(parts[1]),
                float(parts[2]),
                float(parts[3]),
                float(parts[4]),
            )
            if urx <= llx or ury <= lly:
                continue
            if not found:
                minx, miny, maxx, maxy = llx, lly, urx, ury
                found = True
            else:
                minx = min(minx, llx)
                miny = min(miny, lly)
                maxx = max(maxx, urx)
                maxy = max(maxy, ury)
    if not found:
        return None
    return minx, miny, maxx, maxy


def _render_progress(current, total, label):
    is_tty = sys.stdout.isatty()
    bar_w = max(20, min(42, TERM_COLS - 42))
    pct = int(current * 100 / total) if total > 0 else 0
    filled = int(current * bar_w / total) if total > 0 else 0
    pct = min(pct, 100)
    filled = min(filled, bar_w)

    if not is_tty:
        print(f"  {label:<{LABEL_WIDTH}} : {pct:3d}%  ({current}/{total})")
        return

    if current >= total:
        body = "=" * bar_w
        tail = ""
        empty = ""
    elif filled <= 0:
        body = tail = ""
        empty = "-" * bar_w
    else:
        body = "=" * max(0, filled - 1)
        tail = ">"
        empty = "-" * (bar_w - filled)

    if color_enabled():
        bar = f"{BRIGHT_GREEN}{BOLD}{body}{BRIGHT_YELLOW}{BOLD}{tail}{WHITE}{empty}"
        sys.stdout.write(
            f"\r\033[2K  {BRIGHT_CYAN}{BOLD}{label:<{LABEL_WIDTH}}{RESET}"
            f" {BRIGHT_WHITE}{BOLD}:{RESET}"
            f" {BRIGHT_WHITE}[{bar}{RESET}{BRIGHT_WHITE}]{RESET}"
            f" {BRIGHT_YELLOW}{BOLD}{pct:3d}%{RESET}"
            f"  {BRIGHT_WHITE}{current}/{total}{RESET}"
        )
    else:
        sys.stdout.write(
            f"\r  {label:<{LABEL_WIDTH}} : [{body}{tail}{empty}] {pct:3d}%  {current}/{total}"
        )
    sys.stdout.flush()


def _convert_pdf_with_progress(input_f, output_f, first, last, cw, ch, cl, cb, total):
    _render_progress(0, total, "Progress")

    result = subprocess.run(
        [
            "gs",
            "-dSAFER",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=pdfwrite",
            "-dAutoRotatePages=/None",
            "-dFIXEDMEDIA",
            "-dModifiesPageSize=true",
            f"-dDEVICEWIDTHPOINTS={cw}",
            f"-dDEVICEHEIGHTPOINTS={ch}",
            f"-dFirstPage={first}",
            f"-dLastPage={last}",
            "-o",
            output_f,
            "-c",
            f"<</BeginPage{{0 0 {cw} {ch} rectclip -{cl} -{cb} translate}}>> setpagedevice",
            "-f",
            input_f,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    count = 0
    stdout_stream = result.stdout or ""
    for line in stdout_stream.splitlines():
        if re.match(r"^Page\s+\d+\s*$", line):
            count += 1
            _render_progress(min(count, total), total, "Progress")

    if sys.stdout.isatty():
        sys.stdout.write("\r\033[2K")
        sys.stdout.flush()

    return result.returncode


def run(args):
    _init_ui()
    require_commands("gs", "pdfinfo")

    input_file = out_file = bbox_custom = export_range = analyze_pages_spec = ""
    margleft = margtop = margright = margbot = 0.0
    default_analyze_pages = 10

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--in":
            input_file = args[i + 1]
            i += 2
        elif a == "--out":
            out_file = args[i + 1]
            i += 2
        elif a == "--bbox":
            bbox_custom = args[i + 1]
            i += 2
        elif a == "--margins":
            parts = args[i + 1].split()
            if len(parts) != 4:
                _die("--margins requires 4 values: left top right bot")
            margleft, margtop, margright, margbot = (float(x) for x in parts)
            i += 2
        elif a == "--analyze-pages":
            analyze_pages_spec = args[i + 1]
            i += 2
        elif a == "--pages":
            export_range = args[i + 1]
            i += 2
        elif a in ("-h", "--help"):
            print_help("")
            return 0
        else:
            _die(f"Unknown option: {a}")

    if not input_file:
        print_help("")
        return 1
    if not os.path.isfile(input_file):
        _die(f"File not found: {input_file}")

    if not out_file:
        out_file = f"crop-{os.path.basename(input_file)}"

    page_count = _get_page_count(input_file)
    if page_count is None:
        _die("Cannot read page count")
    npages = page_count

    page_mediabox = _get_mediabox(input_file, 1)
    if page_mediabox is None:
        _die("Cannot read MediaBox of page 1")
    page_llx, page_lly, page_urx, page_ury = page_mediabox
    orig_w = page_urx - page_llx
    orig_h = page_ury - page_lly

    export_first, export_last = 1, npages
    if export_range:
        export_first, export_last = _parse_page_range(export_range, npages, "--pages")
    export_total = export_last - export_first + 1

    if analyze_pages_spec:
        analyze_first, analyze_last = _parse_page_range(
            analyze_pages_spec, npages, "--analyze-pages"
        )
    else:
        analyze_first = export_first
        analyze_last = min(export_last, export_first + default_analyze_pages - 1)
    analyze_total = analyze_last - analyze_first + 1

    if bbox_custom:
        parts = bbox_custom.split()
        if len(parts) != 4:
            _die("--bbox requires 4 values: left bot right top")
        left, bot, right, top = (float(x) for x in parts)
        bbox_source = "manual"
        if analyze_pages_spec:
            _warn("--analyze-pages ignored because --bbox was specified")
    else:
        result = _compute_auto_bbox(input_file, analyze_first, analyze_last)
        if result is None:
            _warn("No content detected; using full MediaBox")
            left, bot, right, top = page_llx, page_lly, page_urx, page_ury
        else:
            left, bot, right, top = result
        bbox_source = "automatic"

    raw_left, raw_bot, raw_right, raw_top = left, bot, right, top

    left += margleft
    bot += margbot
    right -= margright
    top -= margtop

    left = max(left, page_llx)
    bot = max(bot, page_lly)
    right = min(right, page_urx)
    top = min(top, page_ury)

    if left < page_llx:
        _die("left is outside MediaBox")
    if bot < page_lly:
        _die("bot is outside MediaBox")
    if left >= right:
        _die("Invalid bbox: left must be < right")
    if bot >= top:
        _die("Invalid bbox: bot must be < top")
    if right > page_urx:
        _die("right exceeds MediaBox")
    if top > page_ury:
        _die("top exceeds MediaBox")

    crop_w = right - left
    crop_h = top - bot
    start_time = time.time()

    icons = _icons()
    _section("PDF Conversion")
    _kv("Input", c(input_file, BRIGHT_WHITE))
    _kv("Output", c(out_file, BRIGHT_WHITE))
    _kv("Document pages", c(str(npages), BRIGHT_WHITE))
    _kv(
        "Export pages",
        f"{c(f'{export_first}-{export_last}', BRIGHT_WHITE)}  {c(f'[{export_total} pages]', BRIGHT_YELLOW)}",
    )
    _kv(
        "Analysis pages",
        f"{c(f'{analyze_first}-{analyze_last}', BRIGHT_WHITE)}  {c(f'[{analyze_total} pages]', BRIGHT_YELLOW)}",
    )
    _kv(
        "Page 1 MediaBox",
        c(_fmt_quad(page_llx, page_lly, page_urx, page_ury), BRIGHT_WHITE),
    )
    _kv("Page 1 size", c(_fmt_size(orig_w, orig_h), BRIGHT_WHITE))
    bbox_str = c(
        f"{icons['bbox']} {_fmt_bbox_line(raw_left, raw_bot, raw_right, raw_top)}",
        BRIGHT_YELLOW + BOLD,
    )
    _kv("BBox detected", f"{bbox_str}  {c(f'[{bbox_source}]', BRIGHT_WHITE)}")
    if any(v != 0 for v in (margleft, margtop, margright, margbot)):
        _kv(
            "Margins applied",
            c(
                f"L={_fmt(margleft)}  T={_fmt(margtop)}  R={_fmt(margright)}  B={_fmt(margbot)}",
                BRIGHT_WHITE,
            ),
        )
    _kv("Final crop", c(_fmt_size(crop_w, crop_h), BRIGHT_GREEN + BOLD))
    print()

    rc = _convert_pdf_with_progress(
        input_file,
        out_file,
        export_first,
        export_last,
        crop_w,
        crop_h,
        left,
        bot,
        export_total,
    )
    if rc != 0:
        _die("Ghostscript conversion failed")

    out_mbox = _get_mediabox(out_file, 1)
    out_media_w = out_media_h = 0
    if out_mbox:
        out_media_w = out_mbox[2] - out_mbox[0]
        out_media_h = out_mbox[3] - out_mbox[1]

    r = subprocess.run(
        ["pdfinfo", "-f", "1", "-l", "1", "-box", out_file],
        capture_output=True,
        text=True,
    )
    out_crop_w = out_crop_h = 0
    for line in r.stdout.splitlines():
        if "CropBox:" in line:
            parts = line.split()
            vals = [float(x) for x in parts[-4:]]
            out_crop_w = vals[2] - vals[0]
            out_crop_h = vals[3] - vals[1]
            break

    elapsed = int(time.time() - start_time)

    _section("Execution summary")
    _kv("Status", c(f"{icons['done']} Completed", BRIGHT_GREEN + BOLD))
    _kv("Input", c(input_file, BRIGHT_WHITE))
    _kv("Output", c(out_file, BRIGHT_WHITE))
    _kv(
        "Pages converted",
        f"{c(str(export_total), BRIGHT_WHITE)}  {c(f'[{export_first}-{export_last}]', BRIGHT_YELLOW)}",
    )
    _kv(
        "BBox used",
        f"{c(_fmt_bbox_line(left, bot, right, top), BRIGHT_YELLOW + BOLD)}  {c(f'[{bbox_source}]', BRIGHT_WHITE)}",
    )
    _kv("Output MediaBox", c(_fmt_size(out_media_w, out_media_h), BRIGHT_WHITE))
    _kv("Output CropBox", c(_fmt_size(out_crop_w, out_crop_h), BRIGHT_WHITE))
    _kv("Duration", c(f"{elapsed}s", BRIGHT_WHITE))
    _hr(_icons()["thick"])

    return 0
