#!/usr/bin/env python3
import os

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch OpenCode CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-opencode [args...] ({version})")
    print()
    print("cli-opencode options:")
    print("  All arguments are passed through to the OpenCode CLI.")
    print("  --help  - Show this help message.")


def run(args):
    require_project_root()
    cmd = ["/usr/bin/opencode"] + args
    os.execvp(cmd[0], cmd)
