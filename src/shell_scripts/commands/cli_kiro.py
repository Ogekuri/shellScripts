#!/usr/bin/env python3
"""@brief Kiro CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
process replacement with user-local Kiro executable.
@satisfies REQ-019, REQ-055, REQ-056
"""

import os
from pathlib import Path

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Kiro CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-kiro [args...] ({version})")
    print()
    print("cli-kiro options:")
    print("  All arguments are passed through to the Kiro CLI.")
    print("  --help  - Show this help message.")


def run(args):
    """@brief Launch Kiro CLI after external executable validation.

    @details Resolves project root and user-local Kiro executable path,
    validates executable availability, then replaces process image.
    @param args {list[str]} Additional CLI args forwarded to Kiro.
    @return {None} Function does not return on successful `os.execvp`.
    @satisfies REQ-019, REQ-055, REQ-056
    """

    require_project_root()
    kiro_bin = str(Path.home() / ".local" / "bin" / "kiro-cli")
    cmd = [kiro_bin] + args
    require_commands(cmd[0])
    os.execvp(cmd[0], cmd)
