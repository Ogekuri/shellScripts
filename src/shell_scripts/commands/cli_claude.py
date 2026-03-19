#!/usr/bin/env python3
import os
from pathlib import Path

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-claude [args...] ({version})")
    print()
    print("cli-claude options:")
    print("  All arguments are passed through to the Claude CLI.")
    print("  --help  - Show this help message.")


def run(args):
    require_project_root()
    claude_bin = Path.home() / ".claude" / "bin" / "claude"
    cmd = [str(claude_bin), "--dangerously-skip-permissions"] + args
    os.execvp(cmd[0], cmd)
