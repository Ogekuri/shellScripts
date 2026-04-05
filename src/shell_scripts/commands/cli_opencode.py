#!/usr/bin/env python3
"""@brief OpenCode CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `opencode`.
@satisfies REQ-018, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch OpenCode CLI in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-opencode [args...] ({version})")
    print()
    print("cli-opencode options:")
    print("  All arguments are passed through to the OpenCode CLI.")
    print("  --help  - Show this help message.")


def run(args):
    """@brief Launch OpenCode CLI after external executable validation.

    @details Resolves project root, checks executable availability for
    `opencode`, then executes pass-through args through blocking subprocess run.
    @param args {list[str]} Additional CLI args forwarded to OpenCode.
    @return {int} Child process return code.
    @satisfies REQ-018, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    cmd = ["opencode"] + args
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
