#!/usr/bin/env python3
"""@brief Meld/GtkSourceView "Highlight" color-scheme generator.

@details Python port of the legacy `bin/Meld_Create_TextHighlight.sh` script.
Discovers GtkSourceView style schemes, generates one `<id>-highlight` scheme
per candidate inheriting the original palette, applies the special
`meld-base` handling (dark palette inheritance from `meld-dark`), and writes
the results into every user style directory with backup plus atomic replace.
The generated XML is byte-identical to the legacy bash implementation.
@satisfies PRJ-008, DES-069, REQ-156, REQ-157, REQ-158, REQ-159, REQ-160,
REQ-161, REQ-162, REQ-163, REQ-164, REQ-165, REQ-166, REQ-167, REQ-168
"""
import argparse
import copy
from datetime import datetime
import importlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

PROGRAM = "shellscripts"
DESCRIPTION = "Create Meld Highlight color schemes for Meld and GtkSourceView."

## @var TARGET_SUBDIRS
#  @brief Home-relative style-directory suffixes receiving generated schemes.
#  @details Ordered user-directory list covering Meld, GtkSourceView 3/4/5,
#  and the Flatpak Meld data tree; every entry receives each generated file.
#  @satisfies REQ-166
TARGET_SUBDIRS = (
    ".local/share/meld/styles",
    ".local/share/gtksourceview-5/styles",
    ".local/share/gtksourceview-4/styles",
    ".local/share/gtksourceview-3.0/styles",
    ".var/app/org.gnome.meld/data/meld/styles",
    ".var/app/org.gnome.meld/data/gtksourceview-5/styles",
    ".var/app/org.gnome.meld/data/gtksourceview-4/styles",
    ".var/app/org.gnome.meld/data/gtksourceview-3.0/styles",
)

## @var SOURCE_SYSTEM_SUBDIRS
#  @brief Absolute system style directories scanned for candidate schemes.
#  @details Read-only discovery roots resolved before the user directories so
#  that same-id user schemes override system schemes during discovery.
#  @satisfies REQ-157
SOURCE_SYSTEM_SUBDIRS = (
    "/usr/share/meld/styles",
    "/usr/share/gtksourceview-5/styles",
    "/usr/share/gtksourceview-4/styles",
    "/usr/share/gtksourceview-3.0/styles",
)

## @var TARGET_DIRS
#  @brief Resolved writable style directories under the user home.
#  @details Computed at import from `TARGET_SUBDIRS` and `Path.home()` exactly
#  like the legacy script; tests MAY monkeypatch this module attribute to
#  redirect generation into fixture directories.
#  @satisfies REQ-166
TARGET_DIRS = [Path.home() / part for part in TARGET_SUBDIRS]

## @var SOURCE_DIRS
#  @brief Resolved scheme discovery directories (system first, user last).
#  @details System directories precede user directories so later user entries
#  overwrite same-id schemes in the discovery map, mirroring the legacy
#  script; tests MAY monkeypatch this module attribute.
#  @satisfies REQ-157
SOURCE_DIRS = [Path(part) for part in SOURCE_SYSTEM_SUBDIRS] + TARGET_DIRS

## @var RED_BG
#  @brief Background color applied to the injected `meld:inline` style.
#  @details Fixed red highlight palette token shared by every generated scheme.
#  @satisfies REQ-160
RED_BG = "#cc0000"

## @var WHITE_FG
#  @brief Foreground color applied to the injected `meld:inline` style.
#  @details Fixed white highlight palette token shared by every generated scheme.
#  @satisfies REQ-160
WHITE_FG = "#ffffff"

## @var _REQUIRED_DARK_STYLES
#  @brief Meld styles the dark palette MUST provide for `meld-base` inheritance.
#  @details Missing membership aborts generation with an explicit error.
#  @satisfies REQ-162
_REQUIRED_DARK_STYLES = {
    "meld:insert",
    "meld:replace",
    "meld:conflict",
    "meld:current-line-highlight",
    "meld:current-chunk-highlight",
}

## @var _SCHEME_ID_PATTERN
#  @brief ASCII scheme-id validation pattern `[\w.-]+` with full match semantics.
#  @details Rejects scheme files whose `id` attribute contains whitespace,
#  separators, or non-ASCII characters.
#  @satisfies REQ-157
_SCHEME_ID_PATTERN = re.compile(r"[\w.-]+", flags=re.ASCII)


def _build_parser():
    """@brief Build the `meld-highlight-theme` argument parser.

    @details Registers the mutually exclusive `--dark`/`--light` palette
    selectors plus `--only-meld-base`; `parse_args` errors terminate with
    exit code `2`, matching the legacy script `argparse` behavior.
    @return {argparse.ArgumentParser} Configured parser instance.
    @satisfies REQ-156
    """
    parser = argparse.ArgumentParser(
        description="Create the Meld Highlight color schemes.",
    )
    theme = parser.add_mutually_exclusive_group()
    theme.add_argument(
        "--dark", action="store_true",
        help="Dark difference palette for Classic (Meld)",
    )
    theme.add_argument(
        "--light", action="store_true",
        help="Light difference palette for Classic (Meld)",
    )
    parser.add_argument(
        "--only-meld-base", action="store_true",
        help="Update only Classic (Meld) Highlight",
    )
    return parser


def all_schemes():
    """@brief Discover candidate style schemes across all source directories.

    @details Iterates `SOURCE_DIRS` in order, parses each `*.xml` file sorted
    by name, silently skips unreadable or non-`style-scheme` roots, validates
    the `id` attribute against `_SCHEME_ID_PATTERN`, resolves the display name
    from `_name`, `name`, or the id, and lets later directories override
    earlier same-id entries. Time complexity O(N log N) per directory over the
    XML file inventory.
    @return {dict[str, tuple[str, xml.etree.ElementTree.Element]]} Mapping
      scheme id to `(display_name, scheme_root_element)`.
    @satisfies REQ-157
    """
    found = {}
    for folder in SOURCE_DIRS:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.xml")):
            try:
                root = ET.parse(path).getroot()
            except (OSError, ET.ParseError):
                continue
            if root.tag != "style-scheme":
                continue
            sid = root.get("id")
            if sid and _SCHEME_ID_PATTERN.fullmatch(sid):
                name = root.get("_name") or root.get("name") or sid
                found[sid] = (name if name.strip() else sid, root)
    return found


def setting(schema, key):
    """@brief Read one GNOME `gsettings` value.

    @details Runs `gsettings get <schema> <key>` with captured output and a
    4-second timeout, returning the stripped stdout on success and `None` on
    failure, timeout, or missing executable.
    @param schema {str} GSettings schema identifier (e.g. `org.gnome.meld`).
    @param key {str} GSettings key name inside the schema.
    @return {str|None} Stripped value text on success; `None` otherwise.
    @satisfies REQ-163
    """
    try:
        result = subprocess.run(
            ("gsettings", "get", schema, key),
            capture_output=True, text=True, check=False, timeout=4,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def using_dark_theme():
    """@brief Auto-detect whether the desktop currently uses a dark theme.

    @details Reproduces the legacy detection chain: first reads the Meld
    `prefer-dark-theme` preference and, when a display server is attached,
    queries the GTK 3 default settings and looks up `theme_bg_color` on a
    probe `Gtk.TextView`, returning darkness when the summed RGB is below
    `1.0`; otherwise falls back to the GNOME `color-scheme` (`prefer-dark`
    substring) and case-insensitive `dark` substrings in the GTK theme name
    or `GTK_THEME` environment variable. All failures degrade to the fallback
    path.
    @return {bool} `True` when the detected desktop palette is dark.
    @satisfies REQ-163
    """
    meld_preference = setting("org.gnome.meld", "prefer-dark-theme")
    try:
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            gi = importlib.import_module("gi")
            gi.require_version("Gtk", "3.0")
            Gtk = importlib.import_module("gi.repository.Gtk")
            initialized = Gtk.init_check()
            initialized = initialized[0] if isinstance(initialized, (tuple, list)) else initialized
            if initialized:
                settings = Gtk.Settings.get_default()
                if settings and meld_preference in ("true", "false"):
                    settings.props.gtk_application_prefer_dark_theme = (meld_preference == "true")
                view = Gtk.TextView()
                exists, rgba = view.get_style_context().lookup_color("theme_bg_color")
                if exists:
                    return rgba.red + rgba.green + rgba.blue < 1.0
    except Exception:
        pass
    colour_scheme = setting("org.gnome.desktop.interface", "color-scheme") or ""
    gtk_theme = setting("org.gnome.desktop.interface", "gtk-theme") or ""
    if "prefer-dark" in colour_scheme:
        return True
    return any("dark" in value.lower() for value in (gtk_theme, os.environ.get("GTK_THEME", "")))


def build_xml(sid, name, dark_palette=None):
    """@brief Build the serialized `<id>-highlight` XML payload for one scheme.

    @details Creates a `style-scheme` root with `id="<sid>-highlight"`,
    `_name="<name> Highlight"`, `parent-scheme="<sid>"`, `version="1.0"`, an
    `author` element `Custom Script`, and a `_description` element
    `<name> con evidenziazione inline rossa`. When `dark_palette` is supplied,
    deep-copies every direct `meld:*` and `map-overlay` style except
    `meld:inline`, aborts on any missing required Meld style, and inserts
    deep copies of every palette `<color>` whose name is referenced by an
    inherited style attribute at child index `2`. Finally appends the fixed
    `meld:inline` style, indents the tree with two spaces, serializes with the
    UTF-8 XML declaration, and validates that inheritance is preserved and no
    `text` style leaked into the output.
    @param sid {str} Source scheme identifier; MUST match `_SCHEME_ID_PATTERN`.
    @param name {str} Source scheme display name.
    @param dark_palette {Element|None} `meld-dark` root element whose styles
      are inherited; `None` produces the plain light payload.
    @return {bytes} Complete XML document bytes terminated by a newline.
    @throws {ValueError} When the dark palette lacks a required Meld style or
      the serialized payload loses `parent-scheme` inheritance or contains a
      `text` style.
    @satisfies REQ-159, REQ-160, REQ-161, REQ-162, REQ-165
    """
    root = ET.Element("style-scheme", {
        "id": sid + "-highlight",
        "_name": name + " Highlight",
        "parent-scheme": sid,
        "version": "1.0",
    })
    ET.SubElement(root, "author").text = "Custom Script"
    ET.SubElement(root, "_description").text = name + " con evidenziazione inline rossa"

    if dark_palette is not None:
        included = set()
        for style in dark_palette.findall("style"):
            key = style.get("name", "")
            if (key.startswith("meld:") or key == "map-overlay") and key != "meld:inline":
                root.append(copy.deepcopy(style))
                included.add(key)
        if _REQUIRED_DARK_STYLES - included:
            raise ValueError(
                "The Meld dark scheme is missing expected styles: "
                + ", ".join(sorted(_REQUIRED_DARK_STYLES - included))
            )

        named = {item.get("name"): item for item in dark_palette.findall("color")}
        attrs = ("foreground", "background", "line-background", "underline-color")
        values = {style.get(attr) for style in root.findall("style") for attr in attrs}
        for cname, colour in named.items():
            if cname in values:
                root.insert(2, copy.deepcopy(colour))

    ET.SubElement(root, "style", {
        "name": "meld:inline", "background": RED_BG, "foreground": WHITE_FG,
    })
    ET.indent(root, space="  ")
    xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"
    parsed = ET.fromstring(xml)
    if parsed.get("parent-scheme") != sid or any(x.get("name") == "text" for x in parsed.findall("style")):
        raise ValueError("Inheritance not preserved for " + sid)
    return xml


def print_help(version):
    """@brief Print command-specific help text.

    @details Renders usage line, option list, and a behavioral summary in
    English, following the shared command help layout.
    @param version {str} Current CLI version token rendered in the usage line.
    @return {None} Writes to stdout.
    @satisfies PRJ-002, REQ-156
    """
    print(f"Usage: {PROGRAM} meld-highlight-theme ({version})")
    print()
    print("meld-highlight-theme options:")
    print("  --help           - Show this help message.")
    print("  --dark           - Use the dark difference palette for Classic (Meld).")
    print("  --light          - Use the light difference palette for Classic (Meld).")
    print("  --only-meld-base - Update only Classic (Meld) Highlight.")
    print()
    print("Creates one '<id>-highlight' scheme for every discovered Meld and")
    print("GtkSourceView style scheme, inheriting the original colors and adding")
    print("a red inline highlight style; Classic (Meld) additionally inherits the")
    print("meld-dark difference styles when the dark palette is selected.")


def run(args):
    """@brief Execute the highlight-theme generation pipeline.

    @details Parses palette arguments, discovers schemes, resolves the dark
    flag from explicit selectors or desktop auto-detection, validates the
    `meld-base`/`meld-dark` preconditions, builds and plans one payload per
    selected scheme, prints the English report block, then writes every
    planned destination with timestamped backup and same-directory atomic
    replace before printing the English summary. Exit code `2` is raised via
    `parser.error` on invalid arguments or missing precondition schemes.
    @param args {list[str]} Command arguments (without the command token).
    @return {int} `0` after a completed generation run.
    @throws {SystemExit} Exit code `2` via `parser.error` when `--dark` and
      `--light` are combined, `--only-meld-base` finds no `meld-base` scheme,
      or the dark palette applies while `meld-dark` is missing.
    @throws {ValueError} Propagated from `build_xml` on payload integrity
      failure.
    @satisfies REQ-156, REQ-157, REQ-158, REQ-159, REQ-160, REQ-161, REQ-162,
    REQ-163, REQ-164, REQ-165, REQ-166, REQ-167, REQ-168
    """
    parser = _build_parser()
    parsed = parser.parse_args(args)

    schemes = all_schemes()
    dark = parsed.dark or (not parsed.light and using_dark_theme())
    if parsed.only_meld_base and "meld-base" not in schemes:
        parser.error("Scheme meld-base not found")
    if dark and "meld-base" in schemes and "meld-dark" not in schemes:
        parser.error("Scheme meld-dark not found")

    planned = []
    rows = []
    for sid, (name, _root) in sorted(schemes.items(), key=lambda item: item[1][0].casefold()):
        if sid.endswith("-highlight") or name.endswith(" Highlight") or sid.startswith("texthighlight"):
            continue
        if parsed.only_meld_base and sid != "meld-base":
            continue
        palette = schemes["meld-dark"][1] if sid == "meld-base" and dark else None
        data = build_xml(sid, name, palette)
        changed = False
        for folder in TARGET_DIRS:
            dest = folder / (sid + "-highlight.xml")
            if dest.is_file() and dest.read_bytes() == data:
                continue
            planned.append((dest, data))
            changed = True
        rows.append((name, changed))

    print("╭──────────────────────────────────────────────────╮")
    print("│            Meld · Highlight Themes              │")
    print("╰──────────────────────────────────────────────────╯")
    print("  Classic (Meld) palette:", "dark" if dark else "light")
    print()
    for name, changed in rows:
        symbol = "✓" if changed else "·"
        status = "updated" if changed else "already present"
        print(f"  {symbol}  {name} → {name} Highlight  ({status})")

    backup_tag = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backups = 0
    for dest, data in planned:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.copy2(dest, dest.with_name(dest.name + ".bak-" + backup_tag))
            backups += 1
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile("wb", dir=dest.parent,
                                             prefix=dest.name + ".tmp-", delete=False) as handle:
                temp_path = handle.name
                handle.write(data)
            os.replace(temp_path, dest)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    print()
    print(f"  Completed: {len(rows)} variants, {len(planned)} files written, {backups} backups.")
    print("  Restart Meld to see the updated schemes.")
    return 0
