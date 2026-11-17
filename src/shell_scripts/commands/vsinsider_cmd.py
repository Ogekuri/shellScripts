#!/usr/bin/env python3
"""@brief VS Code Insiders launcher in project context.

@details Resolves project root, validates VS Code Insiders executable
availability, and performs blocking subprocess invocation.
@satisfies REQ-020, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Open VS Code Insiders in the project root."


def print_help(version):
    print(f"Usage: {PROGRAM} vsinsider [args...] ({version})")
    print()
    print("vsinsider options:")
    print("  [args...]  - Arguments passed through to VS Code Insiders.")
    print("  --help     - Show this help message.")


def run(args):
    """@brief Launch VS Code Insiders after executable validation.

    @details Validates executable availability for VS Code Insiders binary
    and executes the command with project-root working directory.
    @param args {list[str]} Additional CLI args forwarded to VS Code Insiders.
    @return {int} Child process return code.
    @satisfies REQ-020, REQ-055, REQ-056, REQ-064
    """

    project_root = require_project_root()
    cmd = ["/usr/share/code-insiders/bin/code-insiders"] + args + [str(project_root)]
    require_commands(cmd[0])
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode
