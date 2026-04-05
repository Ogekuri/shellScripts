#!/usr/bin/env python3
"""@brief Kiro CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `kiro-cli`.
@satisfies REQ-019, REQ-055, REQ-056, REQ-064
"""

import subprocess

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
    `kiro-cli`, then executes pass-through args through blocking subprocess run.
    @param args {list[str]} Additional CLI args forwarded to Kiro.
    @return {int} Child process return code.
    @satisfies REQ-019, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    cmd = ["kiro-cli"] + args
    require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
