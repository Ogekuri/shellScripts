#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

from shell_scripts.utils import require_project_root, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Find and delete cache directories under the project root."

CACHE_DIRS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".cache",
    ".npm",
    ".parcel-cache",
    ".eslintcache",
    ".sass-cache",
    ".terragrunt-cache",
    "htmlcov",
]


def print_help(version):
    print(f"Usage: {PROGRAM} clean [options] ({version})")
    print()
    print("clean options:")
    print("  <directory>  - Target directory to search (default: git project root).")
    print("  --yes        - Skip confirmation prompt and delete immediately.")
    print("  --help       - Show this help message.")


def run(args):
    project_root = require_project_root()
    target_dir = project_root
    auto_confirm = False

    for arg in args:
        if arg == "--yes":
            auto_confirm = True
        elif not arg.startswith("-"):
            target_dir = Path(arg)
        else:
            print_error(f"Unknown option: {arg}")
            return 1

    os.chdir(project_root)

    print(f"--- Searching for cache directories in: {target_dir} ---")
    print("Please wait, scanning...")

    found = []
    for dir_name in CACHE_DIRS:
        for root, dirs, _ in os.walk(target_dir):
            if dir_name in dirs:
                found.append(os.path.join(root, dir_name))

    if not found:
        print("No cache directories found.")
        return 0

    print()
    print("Found the following directories:")
    print("---------------------------------")
    for path in found:
        print(f" -> {path}")
    print("---------------------------------")
    print(f"Total directories found: {len(found)}")
    print()

    if auto_confirm:
        confirm = "y"
    else:
        try:
            confirm = input(
                "WARNING: Are you sure you want to permanently DELETE "
                "these directories? (y/N): "
            )
        except (EOFError, KeyboardInterrupt):
            print()
            confirm = "n"

    if confirm.lower() == "y":
        print()
        print("Deleting...")
        count = 0
        for path in found:
            shutil.rmtree(path, ignore_errors=True)
            count += 1
            print(f"Deleted: {path}")
        print()
        print(f"Cleanup complete! {count} directories removed.")
    else:
        print()
        print("Operation aborted. No files were touched.")

    return 0
