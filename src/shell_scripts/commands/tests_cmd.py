#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

from shell_scripts.utils import require_project_root, print_info, print_success, print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Run pytest test suite in a Python virtual environment."


def print_help(version):
    print(f"Usage: {PROGRAM} tests [pytest-args...] ({version})")
    print()
    print("tests options:")
    print("  [pytest-args...]  - Arguments passed through to pytest.")
    print("  --help            - Show this help message.")


def run(args):
    project_root = require_project_root()
    os.chdir(project_root)

    venv_dir = project_root / ".venv"

    if not venv_dir.is_dir():
        print_info("Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
        )

        pip = str(venv_dir / "bin" / "pip")
        req_file = project_root / "requirements.txt"

        if req_file.exists():
            print_info("Installing python requirements...")
            subprocess.run(
                [pip, "install", "-r", str(req_file)],
                stdout=subprocess.DEVNULL,
                check=True,
            )

        playwright = str(venv_dir / "bin" / "playwright")
        if os.path.exists(playwright):
            print_info("Installing Playwright Chromium...")
            subprocess.run([playwright, "install", "chromium"])

    python = str(venv_dir / "bin" / "python3")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src") + ":" + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [python, "-m", "pytest"] + args,
        env=env,
    )

    if result.returncode != 0:
        return result.returncode

    print_success("Main test suite OK.")
    return 0
