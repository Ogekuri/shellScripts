#!/usr/bin/env python3
import os

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch GitHub Copilot CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-copilot [args...] ({version})")
    print()
    print("cli-copilot options:")
    print("  All arguments are passed through to the Copilot CLI.")
    print("  --help  - Show this help message.")


def run(args):
    require_project_root()
    cmd = ["/usr/bin/copilot", "--yolo", "--allow-all-tools"] + args
    os.execvp(cmd[0], cmd)
