#!/usr/bin/env python3
"""@brief Virtual-environment recreation workflow with optional dependency install.

@details Ensures required Python executables are available for the active flow
before creating `.venv` and optionally running `pip install -r requirements.txt`.
@satisfies REQ-038, REQ-055, REQ-056
"""

import os
import sys
import shutil
import subprocess

from shell_scripts.utils import (
    require_project_root,
    print_info,
    print_success,
    require_commands,
)

PROGRAM = "shellscripts"
DESCRIPTION = "Create or recreate Python virtual environment with requirements."


def print_help(version):
    print(f"Usage: {PROGRAM} venv [options] ({version})")
    print()
    print("venv options:")
    print("  --force  - Force recreation even if .venv exists.")
    print("  --help   - Show this help message.")


def run(args):
    """@brief Recreate virtual environment with executable pre-checks.

    @details Validates `sys.executable` and flow-conditional `pip` executable
    before corresponding subprocess invocations.
    @param args {list[str]} Command arguments (`--force` accepted).
    @return {int} `0` on successful execution.
    @satisfies REQ-038, REQ-055, REQ-056
    """

    force = "--force" in args
    require_commands(sys.executable)
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
        require_commands(pip)
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
