#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import tempfile

from shell_scripts.utils import require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Split PDF into parts by page format changes."


def print_help(version):
    print(f"Usage: {PROGRAM} pdf-split-by-format <file1.pdf> [file2.pdf ...] ({version})")
    print()
    print("pdf-split-by-format options:")
    print("  <files...>  - Input PDF files to split.")
    print("  --help      - Show this help message.")


def _get_page_formats(pdf, total_pages):
    r = subprocess.run(
        ["pdfinfo", "-f", "1", "-l", str(total_pages), pdf],
        capture_output=True, text=True, stderr=subprocess.DEVNULL,
    )
    formats = []
    for line in r.stdout.splitlines():
        if re.search(r"Page\s+.*size:", line):
            fmt = re.sub(r"Page\s+\d+\s+size:\s*", "", line).strip()
            formats.append(fmt)
    return formats


def _get_total_pages(pdf):
    r = subprocess.run(
        ["pdfinfo", pdf], capture_output=True, text=True, stderr=subprocess.DEVNULL,
    )
    for line in r.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    return None


def _has_toc(pdf):
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp_path = tmp.name
        subprocess.run(
            ["qpdf", "--object-streams=disable", pdf, tmp_path],
            capture_output=True,
        )
        r = subprocess.run(
            ["pdftk", tmp_path, "dump_data"],
            capture_output=True, text=True,
        )
        os.unlink(tmp_path)
        return "BookmarkBegin" in r.stdout
    except Exception:
        return False


def _extract_toc_for_range(data_file, start, end):
    lines = []
    entries = []
    with open(data_file) as f:
        content = f.read()

    level = title = page = ""
    for line in content.splitlines():
        if line == "BookmarkBegin":
            if level and page:
                p = int(page)
                if start <= p <= end:
                    entries.append((level, title, str(p - start + 1)))
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
            entries.append((level, title, str(p - start + 1)))

    result = []
    for lv, ti, pg in entries:
        result.append("BookmarkBegin")
        if ti:
            result.append(f"BookmarkTitle: {ti}")
        if lv:
            result.append(f"BookmarkLevel: {lv}")
        result.append(f"BookmarkPageNumber: {pg}")
    return "\n".join(result)


def _apply_toc(output_file, toc_content):
    if not toc_content.strip():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".info", delete=False) as f:
        f.write(toc_content)
        info_file = f.name
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as stripped_f:
            stripped = stripped_f.name
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as toc_f:
            with_toc = toc_f.name

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
                os.unlink(with_toc)
                print(f"   [!] Warning: unable to update TOC for '{output_file}'.")
        os.unlink(stripped)
    except Exception:
        pass
    finally:
        os.unlink(info_file)


def run(args):
    if not args:
        print_error("No PDF files specified.")
        print_help("")
        return 1

    require_commands("qpdf", "pdfinfo", "pdftk")

    for input_pdf in args:
        print("=" * 50)

        if not os.path.isfile(input_pdf):
            print(f"Warning: File '{input_pdf}' does not exist. Skipping...")
            continue

        print(f"Processing: {input_pdf}")
        basename = os.path.splitext(os.path.basename(input_pdf))[0]

        total_pages = _get_total_pages(input_pdf)
        if total_pages is None:
            print(f"Error: Cannot read pages from '{input_pdf}'. Skipping...")
            continue

        print(f"Analyzing {total_pages} pages...")
        formats = _get_page_formats(input_pdf, total_pages)

        unique = set(formats)
        if len(unique) <= 1:
            print(f"-> INFO: All pages have the same format: [{formats[0] if formats else 'unknown'}].")
            print("-> No splitting needed. Moving to next...")
            continue

        has_toc = _has_toc(input_pdf)
        data_file = None
        if has_toc:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_pdf = tmp.name
            subprocess.run(
                ["qpdf", "--object-streams=disable", input_pdf, tmp_pdf],
                capture_output=True,
            )
            data_file = tempfile.mktemp()
            subprocess.run(
                ["pdftk", tmp_pdf, "dump_data", "output", data_file],
                capture_output=True,
            )
            os.unlink(tmp_pdf)

        start_page = 1
        chunk_num = 1
        prev_format = formats[0]

        for i in range(1, total_pages):
            current_format = formats[i]
            if current_format != prev_format:
                end_page = i
                out_name = f"{basename}_{chunk_num:02d}.pdf"
                print(f"-> Generating: {out_name} (Pages {start_page} - {end_page}) [Format: {prev_format}]")
                subprocess.run(
                    ["qpdf", input_pdf, "--pages", ".", f"{start_page}-{end_page}", "--", out_name],
                )
                if has_toc and data_file:
                    toc = _extract_toc_for_range(data_file, start_page, end_page)
                    _apply_toc(out_name, toc)

                start_page = i + 1
                prev_format = current_format
                chunk_num += 1

        out_name = f"{basename}_{chunk_num:02d}.pdf"
        print(f"-> Generating: {out_name} (Pages {start_page} - {total_pages}) [Format: {prev_format}]")
        subprocess.run(
            ["qpdf", input_pdf, "--pages", ".", f"{start_page}-{total_pages}", "--", out_name],
        )
        if has_toc and data_file:
            toc = _extract_toc_for_range(data_file, start_page, total_pages)
            _apply_toc(out_name, toc)
            os.unlink(data_file)

        print(f"-> Splitting of '{input_pdf}' complete: generated {chunk_num} files.")

    print("=" * 50)
    print("Batch processing completed successfully!")
    return 0
