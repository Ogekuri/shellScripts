#!/usr/bin/env python3
"""@brief VS Code launcher in project context with Codex integration.

@details Resolves project root, configures `CODEX_HOME`, validates VS Code
executable availability, and performs blocking subprocess invocation.
@satisfies REQ-020, REQ-021, REQ-055, REQ-056, REQ-064
"""

import os
import subprocess

from shell_scripts.utils import require_project_root, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Open VS Code in the project root with Codex integration."


def print_help(version):
    print(f"Usage: {PROGRAM} vscode [args...] ({version})")
    print()
    print("vscode options:")
    print("  [args...]  - Arguments passed through to VS Code.")
    print("  --help     - Show this help message.")


def run(args):
    """@brief Launch VS Code after executable validation.

    @details Sets `CODEX_HOME`, validates executable availability for VS Code
    binary, and executes the command with project-root working directory.
    @param args {list[str]} Additional CLI args forwarded to VS Code.
    @return {int} Child process return code.
    @satisfies REQ-020, REQ-021, REQ-055, REQ-056, REQ-064
    """

    project_root = require_project_root()
    codex_home = str(project_root / ".codex")
    os.environ["CODEX_HOME"] = codex_home
    cmd = ["/usr/share/code/bin/code"] + args + [str(project_root)]
    require_commands(cmd[0])
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode
