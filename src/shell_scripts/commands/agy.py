#!/usr/bin/env python3
"""@brief Antigravity CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `agy` in YOLO mode
(`--dangerously-skip-permissions`); inline help lists the registered AI CLI
launch commands in alphabetical order.
@satisfies REQ-085, REQ-086, REQ-055, REQ-056, REQ-064
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
DESCRIPTION = "Launch Antigravity CLI in the project context."
## @var AI_CLI_COMMANDS
#  @brief Alphabetically sorted AI CLI launch command tokens rendered in inline help.
#  @details Derived through `sorted()` at import time so token-set edits preserve
#  the REQ-086 alphabetical rendering contract; contains launcher commands only
#  and excludes installer command tokens.
#  @satisfies REQ-086
AI_CLI_COMMANDS = tuple(sorted((
    "agy",
    "claude",
    "codex",
    "copilot",
    "gemini",
    "kiro",
    "opencode",
    "pi",
)))


def print_help(version):
    """@brief Print command-specific help for `agy`.

    @details Emits usage and pass-through argument behavior, then renders the
    AI CLI launch command tokens from `AI_CLI_COMMANDS`, one per line, in
    ascending alphabetical order; does not mutate process state.
    Time complexity O(n) over registered AI CLI token count.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-086
    """

    print(f"Usage: {PROGRAM} agy [args...] ({version})")
    print()
    print("agy options:")
    print("  All arguments are passed through to the Antigravity CLI.")
    print("  --help  - Show this help message.")
    print()
    print("Available AI CLIs (alphabetical order):")
    for command_token in AI_CLI_COMMANDS:
        print(f"  {command_token}")


def run(args):
    """@brief Launch Antigravity CLI in YOLO mode after executable validation.

    @details Resolves project root, builds the fixed command vector
    `[agy, --dangerously-skip-permissions] + args`, resolves the executable
    path via `require_commands`, then executes it through blocking
    `subprocess.run` with inherited stdio. Time complexity O(n) over forwarded
    argument count.
    @param args {list[str]} Additional CLI args forwarded to Antigravity.
    @return {int} Child process return code.
    @satisfies REQ-085, REQ-055, REQ-056, REQ-064
    """

    require_project_root()
    cmd = ["agy", "--dangerously-skip-permissions"] + args
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
