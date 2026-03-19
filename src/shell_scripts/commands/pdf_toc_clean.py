#!/usr/bin/env python3
import os
import subprocess
import tempfile

from shell_scripts.utils import require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Remove out-of-range TOC entries from PDF files."


def print_help(version):
    print(f"Usage: {PROGRAM} pdf-toc-clean <file1.pdf> [file2.pdf ...] ({version})")
    print()
    print("pdf-toc-clean options:")
    print("  <files...>  - Input PDF files to clean.")
    print("  --help      - Show this help message.")
    print()
    print("For each input PDF, writes <basename>_toc-clean.pdf with")
    print("out-of-range TOC entries removed.")


def _filter_bookmarks(dump_content, max_pages):
    result = []
    level = title = page = ""
    for line in dump_content.splitlines():
        if line == "BookmarkBegin":
            if (level.isdigit() and page.isdigit()
                    and 1 <= int(page) <= max_pages):
                result.append("BookmarkBegin")
                result.append(f"BookmarkTitle: {title}")
                result.append(f"BookmarkLevel: {level}")
                result.append(f"BookmarkPageNumber: {page}")
            level = title = page = ""
        elif line.startswith("BookmarkTitle: "):
            title = line[15:]
        elif line.startswith("BookmarkLevel: "):
            level = line.split()[1]
        elif line.startswith("BookmarkPageNumber: "):
            page = line.split()[1]
    if level.isdigit() and page.isdigit() and 1 <= int(page) <= max_pages:
        result.append("BookmarkBegin")
        result.append(f"BookmarkTitle: {title}")
        result.append(f"BookmarkLevel: {level}")
        result.append(f"BookmarkPageNumber: {page}")
    return "\n".join(result)


def _get_num_pages(dump_content):
    for line in dump_content.splitlines():
        if line.startswith("NumberOfPages:"):
            return int(line.split()[1])
    return None


def _has_out_of_range(dump_content, max_pages):
    page = ""
    for line in dump_content.splitlines():
        if line == "BookmarkBegin":
            if page and page.isdigit():
                p = int(page)
                if p < 1 or p > max_pages:
                    return True
            page = ""
        elif line.startswith("BookmarkPageNumber: "):
            page = line.split()[1]
    if page and page.isdigit():
        p = int(page)
        if p < 1 or p > max_pages:
            return True
    return False


def _clean_one(input_pdf):
    if not os.path.isfile(input_pdf):
        print(f"Warning: input file '{input_pdf}' does not exist; skipping.", flush=True)
        return 0

    dir_name = os.path.dirname(input_pdf) or "."
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]
    output_pdf = os.path.join(dir_name, f"{base_name}_toc-clean.pdf")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_pdf = os.path.join(tmp_dir, "prepared.pdf")
        stripped_pdf = os.path.join(tmp_dir, "stripped.pdf")
        dump_file = os.path.join(tmp_dir, "dump.txt")
        bookmarks_file = os.path.join(tmp_dir, "bookmarks.info")
        cleaned_pdf = os.path.join(tmp_dir, "cleaned.pdf")

        subprocess.run(
            ["qpdf", "--object-streams=disable", input_pdf, tmp_pdf],
            capture_output=True,
        )

        r = subprocess.run(
            ["pdftk", tmp_pdf, "dump_data_utf8"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            r = subprocess.run(
                ["pdftk", tmp_pdf, "dump_data"],
                capture_output=True, text=True,
            )
        dump_content = r.stdout

        with open(dump_file, "w") as f:
            f.write(dump_content)

        total_pages = _get_num_pages(dump_content)
        if total_pages is None:
            print_error(f"Unable to read NumberOfPages for '{input_pdf}'.")
            return 1

        subprocess.run(
            ["qpdf", "--empty", "--pages", tmp_pdf, "1-z", "--", stripped_pdf],
            capture_output=True,
        )

        filtered = _filter_bookmarks(dump_content, total_pages)
        with open(bookmarks_file, "w") as f:
            f.write(filtered)

        r = subprocess.run(
            ["pdftk", stripped_pdf, "update_info_utf8", bookmarks_file, "output", cleaned_pdf],
            capture_output=True,
        )
        utf8_ok = r.returncode == 0

        if utf8_ok:
            verify_r = subprocess.run(
                ["pdftk", cleaned_pdf, "dump_data_utf8"],
                capture_output=True, text=True,
            )
            if verify_r.returncode != 0:
                verify_r = subprocess.run(
                    ["pdftk", cleaned_pdf, "dump_data"],
                    capture_output=True, text=True,
                )
            if _has_out_of_range(verify_r.stdout, total_pages):
                r = subprocess.run(
                    ["pdftk", stripped_pdf, "update_info", bookmarks_file, "output", cleaned_pdf],
                    capture_output=True,
                )
                if r.returncode != 0:
                    print_error(f"Unable to apply cleaned TOC for '{input_pdf}'.")
                    return 1
        elif not utf8_ok:
            r = subprocess.run(
                ["pdftk", stripped_pdf, "update_info", bookmarks_file, "output", cleaned_pdf],
                capture_output=True,
            )
            if r.returncode != 0:
                print_error(f"Unable to apply cleaned TOC for '{input_pdf}'.")
                return 1

        subprocess.run(["qpdf", "--linearize", cleaned_pdf, output_pdf])
        print(f"Cleaned TOC: {input_pdf} -> {output_pdf}")

    return 0


def run(args):
    if not args:
        print_error("No PDF files specified.")
        print_help("")
        return 1

    require_commands("pdftk", "qpdf")

    overall = 0
    for pdf in args:
        if _clean_one(pdf) != 0:
            overall = 1

    return overall
