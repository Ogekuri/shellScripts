#!/usr/bin/env python3
"""@brief Kiro CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
process replacement with `kiro-cli`.
@satisfies REQ-019, REQ-055, REQ-056
"""

import os

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

    @details Resolves project root, validates executable availability for
    `kiro-cli`, then replaces process image.
    @param args {list[str]} Additional CLI args forwarded to Kiro.
    @return {None} Function does not return on successful `os.execvp`.
    @satisfies REQ-019, REQ-055, REQ-056
    """

    require_project_root()
    cmd = ["kiro-cli"] + args
    require_commands(cmd[0])
    os.execvp(cmd[0], cmd)
