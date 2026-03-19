#!/usr/bin/env python3
import sys
from pathlib import Path

from shell_scripts.utils import print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Create or update command symlinks in $HOME/bin."


def print_help(version):
    print(f"Usage: {PROGRAM} bin-links [options] ({version})")
    print()
    print("bin-links options:")
    print(
        "  <directory>    - Source directory containing files to link (default: current dir)."
    )
    print("  --dest <dir>   - Destination directory for symlinks (default: $HOME/bin).")
    print("  --help         - Show this help message.")


def run(args):
    src_dir = Path.cwd()
    dest_dir = Path.home() / "bin"

    i = 0
    while i < len(args):
        if args[i] == "--dest":
            if i + 1 >= len(args):
                print_error("--dest requires a directory path.")
                return 1
            dest_dir = Path(args[i + 1])
            i += 2
        elif not args[i].startswith("-"):
            src_dir = Path(args[i])
            i += 1
        else:
            print_error(f"Unknown option: {args[i]}")
            return 1

    if not src_dir.is_dir():
        print_error(f"Source directory not found: {src_dir}")
        return 1

    dest_dir.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(src_dir.iterdir()):
        if file_path.is_dir():
            continue

        filename = file_path.name
        abs_src = file_path.resolve()
        link_name = filename.removesuffix(".sh")
        target_link = dest_dir / link_name

        print(f"Examining: {filename}...")

        if target_link.exists() or target_link.is_symlink():
            if target_link.is_symlink():
                current_target = target_link.resolve()
                if current_target == abs_src:
                    print(f"  [OK] Link already points correctly to {filename}.")
                else:
                    print("  [UPDATE] Link points elsewhere. Updating...")
                    target_link.unlink()
                    target_link.symlink_to(abs_src)
            else:
                print(
                    f"  [ERROR] '{target_link}' is a regular file. "
                    f"Skipping to avoid data loss.",
                    file=sys.stderr,
                )
        else:
            print("  [NEW] Creating symlink...")
            target_link.symlink_to(abs_src)

    print("--- Operation completed ---")
    return 0
