#!/usr/bin/env python3
import os

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Open VS Code Insiders in the project root with Codex integration."


def print_help(version):
    print(f"Usage: {PROGRAM} vsinsider [args...] ({version})")
    print()
    print("vsinsider options:")
    print("  [args...]  - Arguments passed through to VS Code Insiders.")
    print("  --help     - Show this help message.")


def run(args):
    project_root = require_project_root()
    os.chdir(project_root)
    codex_home = str(project_root / ".codex")
    os.environ["CODEX_HOME"] = codex_home
    cmd = ["/usr/share/code-insiders/bin/code-insiders"] + args + [str(project_root)]
    os.execvp(cmd[0], cmd)
