#!/usr/bin/env python3
import os

from shell_scripts.utils import require_project_root

PROGRAM = "shellscripts"
DESCRIPTION = "Launch OpenAI Codex CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-codex [args...] ({version})")
    print()
    print("cli-codex options:")
    print("  All arguments are passed through to the Codex CLI.")
    print("  --help  - Show this help message.")


def run(args):
    project_root = require_project_root()
    codex_home = str(project_root / ".codex")
    os.environ["CODEX_HOME"] = codex_home
    cmd = ["/usr/bin/codex", "--yolo"] + args
    os.execvp(cmd[0], cmd)
