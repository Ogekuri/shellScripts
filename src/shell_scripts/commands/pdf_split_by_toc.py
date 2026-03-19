#!/usr/bin/env python3
import os
import re
import subprocess
import tempfile

from shell_scripts.utils import require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Split PDF into chapters by TOC level-1 entries."


def print_help(version):
    print(f"Usage: {PROGRAM} pdf-split-by-toc <document.pdf> ({version})")
    print()
    print("pdf-split-by-toc options:")
    print("  <document.pdf>  - Input PDF file (required).")
    print("  --help          - Show this help message.")


def _parse_level1_toc(dump_content):
    entries = []
    level = title = page = ""
    for line in dump_content.splitlines():
        if line == "BookmarkBegin":
            if level == "1" and page:
                entries.append((int(page), title))
            level = title = page = ""
        elif line.startswith("BookmarkTitle: "):
            title = line[15:]
        elif line.startswith("BookmarkLevel: "):
            level = line.split()[1]
        elif line.startswith("BookmarkPageNumber: "):
            page = line.split()[1]
    if level == "1" and page:
        entries.append((int(page), title))
    return entries


def _extract_toc_for_range(dump_content, start, end):
    lines = []
    level = title = page = ""
    for line in dump_content.splitlines():
        if line == "BookmarkBegin":
            if level and page:
                p = int(page)
                if start <= p <= end:
                    lines.append("BookmarkBegin")
                    if title:
                        lines.append(f"BookmarkTitle: {title}")
                    if level:
                        lines.append(f"BookmarkLevel: {level}")
                    lines.append(f"BookmarkPageNumber: {p - start + 1}")
            level = title = page = ""
        elif line.startswith("BookmarkTitle: "):
            title = line[15:]
        elif line.startswith("BookmarkLevel: "):
            level = line.split()[1]
        elif line.startswith("BookmarkPageNumber: "):
            page = line.split()[1]
    if level and page:
        p = int(page)
        if start <= p <= end:
            lines.append("BookmarkBegin")
            if title:
                lines.append(f"BookmarkTitle: {title}")
            if level:
                lines.append(f"BookmarkLevel: {level}")
            lines.append(f"BookmarkPageNumber: {p - start + 1}")
    return "\n".join(lines)


def _sanitize_title(title):
    safe = re.sub(r"[^A-Za-z0-9]", "-", title)
    safe = re.sub(r"-+", "-", safe)
    return safe.strip("-")


def _apply_toc_to_file(output_file, toc_content):
    if not toc_content.strip():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".info", delete=False) as f:
        f.write(toc_content)
        info_file = f.name
    try:
        stripped = tempfile.mktemp(suffix=".pdf")
        with_toc = tempfile.mktemp(suffix=".pdf")
        r1 = subprocess.run(
            ["qpdf", "--empty", "--pages", output_file, "1-z", "--", stripped],
            capture_output=True,
        )
        if r1.returncode == 0:
            r2 = subprocess.run(
                ["pdftk", stripped, "update_info", info_file, "output", with_toc],
                capture_output=True,
            )
            if r2.returncode == 0:
                os.replace(with_toc, output_file)
            else:
                if os.path.exists(with_toc):
                    os.unlink(with_toc)
                print(f"   [!] Warning: unable to update TOC for '{output_file}'.")
        if os.path.exists(stripped):
            os.unlink(stripped)
    finally:
        os.unlink(info_file)


def run(args):
    if not args or args[0].startswith("-"):
        print_error("Input PDF file required.")
        print_help("")
        return 1

    require_commands("pdftk", "qpdf")

    input_file = args[0]
    if not os.path.isfile(input_file):
        print_error(f"File not found: {input_file}")
        return 1

    basename = os.path.splitext(os.path.basename(input_file))[0]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_pdf = os.path.join(tmp_dir, "prepared.pdf")
        data_file = os.path.join(tmp_dir, "data.txt")

        print("Preparing document (disabling Object Streams for TOC reading)...")
        r = subprocess.run(
            ["qpdf", "--object-streams=disable", input_file, tmp_pdf],
            capture_output=True,
        )
        if r.returncode != 0:
            print_error("Error during initial processing with qpdf.")
            return 1

        print("Extracting TOC data...")
        subprocess.run(
            ["pdftk", tmp_pdf, "dump_data", "output", data_file],
            capture_output=True,
        )

        with open(data_file) as f:
            dump_content = f.read()

        if "BookmarkBegin" not in dump_content:
            print_error("No TOC found even after decompression.")
            print("The PDF may use 'Named Destinations' instead of explicit page numbers.")
            return 1

        total_pages = None
        for line in dump_content.splitlines():
            if line.startswith("NumberOfPages:"):
                total_pages = int(line.split()[1])
                break

        if total_pages is None:
            print_error("Cannot read total pages.")
            return 1

        print(f"Document has {total_pages} total pages.")

        toc_entries = _parse_level1_toc(dump_content)
        if not toc_entries:
            print_error("TOC found, but no valid level-1 entries with explicit pages.")
            return 1

        num_sections = len(toc_entries)
        print(f"Found {num_sections} level-1 chapters. Starting split...")

        for i, (start_page, title) in enumerate(toc_entries):
            if i + 1 < num_sections:
                next_page = toc_entries[i + 1][0]
                end_page = max(next_page - 1, start_page)
            else:
                end_page = total_pages

            safe_title = _sanitize_title(title)
            index_padded = f"{i + 1:02d}"
            output_name = f"{basename}_{index_padded}_{safe_title}.pdf"

            print(f"-> Creating: {output_name} (Pages {start_page} - {end_page})")

            r = subprocess.run(
                ["qpdf", input_file, "--pages", input_file,
                 f"{start_page}-{end_page}", "--", output_name],
            )
            if r.returncode != 0:
                print(f"   [!] Error extracting section '{title}'")
                continue

            toc_content = _extract_toc_for_range(dump_content, start_page, end_page)
            _apply_toc_to_file(output_name, toc_content)

    print("---")
    print("Split completed successfully!")
    return 0
