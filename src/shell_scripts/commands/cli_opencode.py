#!/usr/bin/env python3
"""@brief OpenCode CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
process replacement with `opencode`.
@satisfies REQ-018, REQ-055, REQ-056
"""

import os

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
    `opencode`, then replaces process image with pass-through args.
    @param args {list[str]} Additional CLI args forwarded to OpenCode.
    @return {None} Function does not return on successful `os.execvp`.
    @satisfies REQ-018, REQ-055, REQ-056
    """

    require_project_root()
    cmd = ["opencode"] + args
    require_commands(cmd[0])
    os.execvp(cmd[0], cmd)
