#!/usr/bin/env python3
import os
import subprocess
import tempfile

from shell_scripts.utils import require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Merge multiple PDF files preserving table of contents."


def print_help(version):
    print(
        f"Usage: {PROGRAM} pdf-merge [-o output.pdf] file1.pdf file2.pdf ... ({version})"
    )
    print()
    print("pdf-merge options:")
    print("  -o, --output <file>  - Output filename (default: documento_unito.pdf).")
    print("  <files...>           - Input PDF files to merge.")
    print("  --help               - Show this help message.")


def _parse_bookmarks(dump_file):
    entries = []
    level = title = page = ""
    with open(dump_file) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "BookmarkBegin":
                if level and page:
                    entries.append((level, title, page))
                level = title = page = ""
            elif line.startswith("BookmarkTitle: "):
                title = line[15:]
            elif line.startswith("BookmarkLevel: "):
                level = line.split()[1]
            elif line.startswith("BookmarkPageNumber: "):
                page = line.split()[1]
    if level and page:
        entries.append((level, title, page))
    return entries


def _get_num_pages(dump_file):
    with open(dump_file) as f:
        for line in f:
            if line.startswith("NumberOfPages:"):
                return int(line.split()[1])
    return None


def run(args):
    require_commands("pdftk", "qpdf")

    output_file = "documento_unito.pdf"
    input_files = []

    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            output_file = args[i + 1]
            i += 2
        else:
            input_files.append(args[i])
            i += 1

    if not input_files:
        print_error("No PDF files specified.")
        print_help("")
        return 1

    for f in input_files:
        if not os.path.isfile(f):
            print_error(f"File not found: {f}")
            return 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Preparing {len(input_files)} files for merge...")
        print("(Temporarily disabling compression to preserve TOC)")

        decompressed = []
        for idx, f in enumerate(input_files):
            safe_name = f"{idx:04d}_part.pdf"
            tmp_file = os.path.join(tmp_dir, safe_name)
            r = subprocess.run(["qpdf", "--object-streams=disable", f, tmp_file])
            if r.returncode != 0:
                print_error(f"Error preparing file: {f}")
                return 1
            decompressed.append(tmp_file)

        merged_raw = os.path.join(tmp_dir, "merged_unoptimized.pdf")
        r = subprocess.run(["pdftk"] + decompressed + ["cat", "output", merged_raw])
        if r.returncode != 0:
            print_error("Error during merge with pdftk.")
            return 1

        merge_input = merged_raw
        bookmarks_file = os.path.join(tmp_dir, "merged_bookmarks.info")
        page_offset = 0
        seen = set()
        all_bookmarks = []

        for f in decompressed:
            dump_file = os.path.join(
                tmp_dir, os.path.basename(f).replace(".pdf", ".dump.txt")
            )
            r = subprocess.run(
                ["pdftk", f, "dump_data_utf8", "output", dump_file],
                capture_output=True,
            )
            if r.returncode != 0:
                subprocess.run(
                    ["pdftk", f, "dump_data", "output", dump_file],
                    capture_output=True,
                )

            file_pages = _get_num_pages(dump_file)
            if file_pages is None:
                print_error("Unable to read NumberOfPages while rebuilding TOC.")
                return 1

            entries = _parse_bookmarks(dump_file)
            for level, title, page in entries:
                adj_page = int(page) + page_offset
                key = f"{level}|{adj_page}|{title}"
                if key not in seen:
                    seen.add(key)
                    all_bookmarks.append((level, title, str(adj_page)))

            page_offset += file_pages

        with open(bookmarks_file, "w") as bf:
            for level, title, page in all_bookmarks:
                bf.write("BookmarkBegin\n")
                bf.write(f"BookmarkTitle: {title}\n")
                bf.write(f"BookmarkLevel: {level}\n")
                bf.write(f"BookmarkPageNumber: {page}\n")

        if os.path.getsize(bookmarks_file) > 0:
            merged_bm = os.path.join(tmp_dir, "merged_with_bookmarks.pdf")
            r = subprocess.run(
                [
                    "pdftk",
                    merge_input,
                    "update_info_utf8",
                    bookmarks_file,
                    "output",
                    merged_bm,
                ],
                capture_output=True,
            )
            if r.returncode == 0:
                merge_input = merged_bm
            else:
                r = subprocess.run(
                    [
                        "pdftk",
                        merge_input,
                        "update_info",
                        bookmarks_file,
                        "output",
                        merged_bm,
                    ],
                    capture_output=True,
                )
                if r.returncode == 0:
                    merge_input = merged_bm
                else:
                    print_error("Unable to apply rebuilt TOC to merged PDF.")
                    return 1

        print("Optimizing and compressing final file...")
        r = subprocess.run(["qpdf", "--linearize", merge_input, output_file])
        if r.returncode != 0:
            print_error("Error during final optimization.")
            return 1

    print("---")
    print(f"Merge completed successfully with TOC preserved! Saved as: {output_file}")
    return 0
