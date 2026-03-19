#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path

from shell_scripts.utils import require_project_root, print_info, print_success, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Create or recreate Python virtual environment with requirements."


def print_help(version):
    print(f"Usage: {PROGRAM} venv [options] ({version})")
    print()
    print("venv options:")
    print("  --force  - Force recreation even if .venv exists.")
    print("  --help   - Show this help message.")


def run(args):
    force = "--force" in args
    project_root = require_project_root()
    os.chdir(project_root)

    print(f"Run on path: {project_root}")

    venv_dir = project_root / ".venv"

    if venv_dir.is_dir():
        if force:
            print_info("Removing old virtual environment...")
            shutil.rmtree(venv_dir)
        else:
            print_info("Removing old virtual environment...")
            shutil.rmtree(venv_dir)

    print_info("Creating virtual environment...")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
    )
    print_success("Virtual environment created.")

    pip = str(venv_dir / "bin" / "pip")
    req_file = project_root / "requirements.txt"

    if req_file.exists():
        print_info("Installing python requirements...")
        subprocess.run(
            [pip, "install", "-r", str(req_file)],
            stdout=subprocess.DEVNULL,
            check=True,
        )
        print_success("Requirements installed.")
    else:
        print_info("No requirements.txt found, skipping pip install.")

    return 0
