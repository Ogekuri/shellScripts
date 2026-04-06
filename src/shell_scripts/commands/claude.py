#!/usr/bin/env python3
"""@brief Claude CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of user-local Claude binary.
@satisfies REQ-017, REQ-055, REQ-056, REQ-064
"""

import subprocess
from pathlib import Path

from shell_scripts.utils import require_project_root, require_commands

## @var PROGRAM
#  @brief Base CLI program name used in help output.
#  @details Constant identifier for usage-line rendering in command help.
PROGRAM = "shellscripts"
## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."


def print_help(version):
    """@brief Print command-specific help for `claude`.

    @details Emits usage and pass-through argument behavior for deterministic
    terminal rendering; does not mutate process state.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """

    print(f"Usage: {PROGRAM} claude [args...] ({version})")
    print()
    print("claude options:")
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
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
