#!/usr/bin/env python3
import os
from pathlib import Path

from shell_scripts.utils import require_commands, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Tile PDF to A4 pages at 90% scale using plakativ."


def print_help(version):
    print(f"Usage: {PROGRAM} pdf-tiler-090 <input.pdf> ({version})")
    print()
    print("pdf-tiler-090 options:")
    print("  <input.pdf>  - Input PDF file (required).")
    print("  --help       - Show this help message.")
    print()
    print("Outputs <basename>_tiled-A4.pdf in the same directory as the input.")


def run(args):
    if not args or args[0].startswith("-"):
        print_error("Input PDF file required.")
        print_help("")
        return 1

    require_commands("plakativ")

    input_file = Path(args[0])
    if not input_file.is_file():
        print_error(f"File not found: {input_file}")
        return 1

    output_file = input_file.parent / f"{input_file.stem}_tiled-A4.pdf"

    cmd = [
        "plakativ",
        "--factor",
        "0.90",
        "--pagesize",
        "A4",
        "--border",
        "5mm",
        "--cutting-guides",
        "-o",
        str(output_file),
        str(input_file),
    ]
    os.execvp(cmd[0], cmd)
