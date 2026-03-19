#!/usr/bin/env python3
import os

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Google Gemini CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-gemini [args...] ({version})")
    print()
    print("cli-gemini options:")
    print("  All arguments are passed through to the Gemini CLI.")
    print("  --help  - Show this help message.")


def run(args):
    require_project_root()
    cmd = ["/usr/bin/gemini", "--yolo"] + args
    os.execvp(cmd[0], cmd)
