#!/usr/bin/env python3
import os
from pathlib import Path

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Kiro CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-kiro [args...] ({version})")
    print()
    print("cli-kiro options:")
    print("  All arguments are passed through to the Kiro CLI.")
    print("  --help  - Show this help message.")


def run(args):
    require_project_root()
    kiro_bin = str(Path.home() / ".local" / "bin" / "kiro-cli")
    cmd = [kiro_bin] + args
    os.execvp(cmd[0], cmd)
