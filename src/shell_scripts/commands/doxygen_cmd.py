#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from shell_scripts.utils import require_project_root, require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Generate Doxygen documentation (HTML, PDF, Markdown)."


def print_help(version):
    print(f"Usage: {PROGRAM} doxygen ({version})")
    print()
    print("doxygen options:")
    print("  --help  - Show this help message.")
    print()
    print("Generates HTML, PDF, and Markdown documentation in doxygen/ directory.")
    print("Requires: doxygen, make, pdflatex.")


def _supports_generate_markdown():
    try:
        result = subprocess.run(
            ["doxygen", "-x"],
            capture_output=True, text=True, timeout=10,
        )
        return "GENERATE_MARKDOWN" in result.stdout
    except Exception:
        return False


def _write_doxyfile(path, project_root, src_dir, doxygen_dir, has_md):
    content = f"""PROJECT_NAME           = "{project_root.name}"
OUTPUT_DIRECTORY       = "{doxygen_dir}"
INPUT                  = "{src_dir}"
FILE_PATTERNS          = *.py *.sh *.js *.ts *.go *.java *.c *.cpp *.h *.hpp *.rb *.php *.rs *.swift *.kt *.scala *.lua *.r *.m *.mm *.cs
RECURSIVE              = YES
EXTRACT_ALL            = YES
EXTRACT_PRIVATE        = YES
EXTRACT_STATIC         = YES
EXTRACT_LOCAL_CLASSES  = YES
EXTRACT_ANON_NSPACES   = YES
JAVADOC_AUTOBRIEF      = YES
MULTILINE_CPP_IS_BRIEF = YES
SORT_MEMBER_DOCS       = YES
SORT_BRIEF_DOCS        = YES
FULL_PATH_NAMES        = NO
STRIP_FROM_PATH        = "{project_root}"
WARN_IF_UNDOCUMENTED   = NO
WARN_IF_DOC_ERROR      = YES
WARN_NO_PARAMDOC       = NO
QUIET                  = YES
GENERATE_HTML          = YES
HTML_OUTPUT            = html
GENERATE_LATEX         = YES
LATEX_OUTPUT           = latex
USE_PDFLATEX           = YES
GENERATE_XML           = YES
XML_OUTPUT             = xml
MARKDOWN_ID_STYLE      = GITHUB
TOC_INCLUDE_HEADINGS   = 3
"""
    if has_md:
        content += "GENERATE_MARKDOWN      = YES\nMARKDOWN_OUTPUT        = markdown\n"

    Path(path).write_text(content)


def _generate_markdown_fallback(xml_dir, markdown_dir):
    markdown_dir.mkdir(parents=True, exist_ok=True)
    index_xml = xml_dir / "index.xml"
    if not index_xml.exists():
        return

    root = ET.parse(str(index_xml)).getroot()
    entries = []
    for compound in root.findall("compound"):
        name = (compound.findtext("name") or "").strip()
        kind = (compound.get("kind") or "").strip()
        refid = (compound.get("refid") or "").strip()
        if name:
            entries.append((kind, name, refid))

    entries.sort(key=lambda item: (item[0], item[1]))
    lines = ["# Doxygen Markdown Index", "", "Generated from Doxygen XML output.", ""]
    for kind, name, refid in entries:
        lines.append(f"- `{kind}` `{name}` (`{refid}`)")

    (markdown_dir / "index.md").write_text("\n".join(lines) + "\n")


def run(args):
    project_root = require_project_root()
    os.chdir(project_root)

    require_commands("doxygen")

    src_dir = project_root / "src"
    doxygen_dir = project_root / "doxygen"
    html_dir = doxygen_dir / "html"
    markdown_dir = doxygen_dir / "markdown"
    pdf_dir = doxygen_dir / "pdf"
    latex_dir = doxygen_dir / "latex"
    xml_dir = doxygen_dir / "xml"

    if not src_dir.is_dir():
        print_error(f"Source directory not found: {src_dir}")
        return 1

    has_md = _supports_generate_markdown()

    for d in (html_dir, markdown_dir, pdf_dir, latex_dir, xml_dir):
        if d.exists():
            shutil.rmtree(d)
    doxygen_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        doxyfile = f.name
    try:
        _write_doxyfile(doxyfile, project_root, src_dir, doxygen_dir, has_md)
        result = subprocess.run(["doxygen", doxyfile])
        if result.returncode != 0:
            print_error("Doxygen generation failed.")
            return 1
    finally:
        os.unlink(doxyfile)

    if not has_md:
        _generate_markdown_fallback(xml_dir, markdown_dir)

    makefile = latex_dir / "Makefile"
    if makefile.exists():
        from shell_scripts.utils import command_exists
        if command_exists("make") and command_exists("pdflatex"):
            subprocess.run(["make", "-C", str(latex_dir)], stdout=subprocess.DEVNULL)
            refman = latex_dir / "refman.pdf"
            if refman.exists():
                shutil.copy2(str(refman), str(pdf_dir / "refman.pdf"))
            else:
                print_error(f"PDF artifact not generated: {refman}")
        else:
            print_error("'make' or 'pdflatex' not found; skipping PDF build.")

    print(f"Generated: {html_dir}")
    print(f"Generated: {markdown_dir}")
    if (pdf_dir / "refman.pdf").exists():
        print(f"Generated: {pdf_dir / 'refman.pdf'}")

    return 0
