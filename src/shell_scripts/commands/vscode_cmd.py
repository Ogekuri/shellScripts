#!/usr/bin/env python3
"""@brief VS Code launcher in project context.

@details Resolves project root, validates VS Code executable availability,
and performs blocking subprocess invocation.
@satisfies REQ-020, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Open VS Code in the project root."


def print_help(version):
    print(f"Usage: {PROGRAM} vscode [args...] ({version})")
    print()
    print("vscode options:")
    print("  [args...]  - Arguments passed through to VS Code.")
    print("  --help     - Show this help message.")


def run(args):
    """@brief Launch VS Code after executable validation.

    @details Validates executable availability for VS Code binary and
    executes the command with project-root working directory.
    @param args {list[str]} Additional CLI args forwarded to VS Code.
    @return {int} Child process return code.
    @satisfies REQ-020, REQ-055, REQ-056, REQ-064
    """

    project_root = require_project_root()
    cmd = ["/usr/share/code/bin/code"] + args + [str(project_root)]
    require_commands(cmd[0])
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode
