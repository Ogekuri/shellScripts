#!/usr/bin/env python3
"""@brief GitHub Copilot CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
process replacement with `/usr/bin/copilot`.
@satisfies REQ-015, REQ-055, REQ-056
"""

import os

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
    `/usr/bin/copilot`, then replaces process image with pass-through args.
    @param args {list[str]} Additional CLI args forwarded to Copilot.
    @return {None} Function does not return on successful `os.execvp`.
    @satisfies REQ-015, REQ-055, REQ-056
    """

    require_project_root()
    cmd = ["/usr/bin/copilot", "--yolo", "--allow-all-tools"] + args
    require_commands(cmd[0])
    os.execvp(cmd[0], cmd)
