#!/usr/bin/env python3
"""@brief GitHub Copilot CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `copilot`.
@satisfies REQ-015, REQ-055, REQ-056, REQ-064
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

## @var PROGRAM
#  @brief Base CLI program name used in help output.
#  @details Constant identifier for usage-line rendering in command help.
PROGRAM = "shellscripts"
## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch GitHub Copilot CLI in the project context."


def print_help(version):
    """@brief Print command-specific help for `copilot`.

    @details Emits usage and pass-through argument behavior for deterministic
    terminal rendering; does not mutate process state.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """

    print(f"Usage: {PROGRAM} copilot [args...] ({version})")
    print()
    print("copilot options:")
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
    cmd = ["copilot", "--yolo", "--allow-all-tools", "--no-auto-update"] + args
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
