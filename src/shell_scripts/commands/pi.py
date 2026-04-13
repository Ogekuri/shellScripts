#!/usr/bin/env python3
"""@brief pi.dev CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `pi`. Forwards every CLI argument unchanged
and never injects implicit `--tools` parameters. Time complexity O(n), where
n is forwarded argument count.
@satisfies REQ-055, REQ-056, REQ-064, REQ-068, REQ-069
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
DESCRIPTION = "Launch pi.dev CLI in the project context."


def print_help(version: str) -> None:
    """@brief Print command-specific help for `pi`.

    @details Emits usage and pass-through argument behavior for deterministic
    terminal rendering; documents that every CLI argument is forwarded to the
    pi.dev CLI without mutation or implicit option injection. Time complexity
    O(1).
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-068, REQ-069
    """

    print(f"Usage: {PROGRAM} pi [args...] ({version})")
    print()
    print("pi options:")
    print("  All arguments are passed through to the pi.dev CLI unchanged.")
    print("  No implicit --tools argument is added by shellscripts.")
    print("  --help  - Show this help message.")


def run(args: list[str]) -> int:
    """@brief Launch pi.dev CLI after external executable validation.

    @details Resolves project root, checks executable availability for `pi`,
    and forwards all CLI arguments unchanged to the child process. The command
    vector shape is `[resolved_pi_exec] + args`. Time complexity O(n), where n
    is forwarded argument count.
    @param args {list[str]} Additional CLI args forwarded to pi.dev.
    @return {int} Child process return code.
    @satisfies REQ-055, REQ-056, REQ-064, REQ-068, REQ-069
    """

    require_project_root()
    resolved_exec = require_commands("pi")
    result = subprocess.run([resolved_exec, *args])
    return result.returncode
