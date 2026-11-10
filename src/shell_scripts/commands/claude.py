#!/usr/bin/env python3
"""@brief Claude CLI launcher in YOLO mode via the shared registry launcher.

@details Thin YOLO command module binding the `claude` registry record and
delegating project-root enforcement, PATH-based executable validation, inline
help rendering, and blocking subprocess invocation to `_yolo_common`.
@satisfies REQ-017, DES-030, DES-031, DES-008
"""

from shell_scripts.commands._yolo_common import (
    get_yolo_spec,
    print_yolo_help,
    run_yolo_cli,
)

## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch Claude CLI with skip-permissions in the project context."
## @var SPEC
#  @brief Declarative YOLO CLI record bound to the `claude` command token.
#  @satisfies DES-030, REQ-017
SPEC = get_yolo_spec("claude")


def print_help(version: str) -> None:
    """@brief Print command-specific help for `claude`.

    @details Delegates to the shared YOLO help renderer, which emits the
    executed option documentation and the alphabetical YOLO CLI registry.
    Time complexity O(n) over registered YOLO CLI record count.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-086, REQ-092
    """
    print_yolo_help(SPEC.command, version, DESCRIPTION)


def run(args: list[str]) -> int:
    """@brief Launch Claude CLI in YOLO mode after executable validation.

    @details Delegates to the shared YOLO runner executing the PATH-resolved
    `claude --dangerously-skip-permissions` plus pass-through args through
    blocking subprocess run with inherited stdio. Time complexity O(n) over
    forwarded argument count.
    @param args {list[str]} Additional CLI args forwarded to Claude.
    @return {int} Child process return code.
    @satisfies REQ-017, REQ-055, REQ-056, REQ-064
    """
    return run_yolo_cli(SPEC.command, args)
