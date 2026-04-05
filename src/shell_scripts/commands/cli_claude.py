#!/usr/bin/env python3
"""@brief Claude CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of user-local Claude binary.
@satisfies REQ-017, REQ-055, REQ-056, REQ-064
"""

import subprocess
from pathlib import Path

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."


def print_help(version):
    print(f"Usage: {PROGRAM} cli-claude [args...] ({version})")
    print()
    print("cli-claude options:")
    print("  All arguments are passed through to the Claude CLI.")
    print("  --help  - Show this help message.")


def run(args):
    """@brief Launch Claude CLI after external executable validation.

    @details Resolves project root, resolves user-local Claude executable path,
    validates executable availability, then executes command via subprocess.
    @param args {list[str]} Additional CLI args forwarded to Claude.
    @return {int} Child process return code.
    @satisfies REQ-017, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    claude_bin = Path.home() / ".claude" / "bin" / "claude"
    cmd = [str(claude_bin), "--dangerously-skip-permissions"] + args
    require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
