#!/usr/bin/env python3
"""@brief GitHub Copilot CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `copilot`.
@satisfies REQ-015, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch GitHub Copilot CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-copilot [args...] ({version})")
    print()
    print("cli-copilot options:")
    print("  All arguments are passed through to the Copilot CLI.")
    print("  --help  - Show this help message.")


def run(args):
    """@brief Launch Copilot CLI after external executable validation.

    @details Resolves project root, checks executable availability for
    `copilot`, then executes pass-through args through blocking subprocess run.
    @param args {list[str]} Additional CLI args forwarded to Copilot.
    @return {int} Child process return code.
    @satisfies REQ-015, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    cmd = ["copilot", "--yolo", "--allow-all-tools"] + args
    require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
