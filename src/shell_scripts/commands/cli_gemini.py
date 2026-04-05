#!/usr/bin/env python3
"""@brief Google Gemini CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `gemini`.
@satisfies REQ-016, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Google Gemini CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-gemini [args...] ({version})")
    print()
    print("cli-gemini options:")
    print("  All arguments are passed through to the Gemini CLI.")
    print("  --help  - Show this help message.")


def run(args):
    """@brief Launch Gemini CLI after external executable validation.

    @details Resolves project root, checks executable availability for
    `gemini`, then executes pass-through args through blocking subprocess run.
    @param args {list[str]} Additional CLI args forwarded to Gemini.
    @return {int} Child process return code.
    @satisfies REQ-016, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    cmd = ["gemini", "--yolo"] + args
    require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
