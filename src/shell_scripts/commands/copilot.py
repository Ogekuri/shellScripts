#!/usr/bin/env python3
"""@brief GitHub Copilot CLI launcher in YOLO mode via the shared launcher.

@details Thin YOLO command module binding the `copilot` registry record and
delegating project-root enforcement, executable validation, inline help
rendering, and blocking subprocess invocation to `_yolo_common`. The accepted
alternative `--allow-all` option is documented in inline help only.
@satisfies REQ-015, REQ-093, DES-030, DES-031, DES-008
"""

from shell_scripts.commands._yolo_common import (
    get_yolo_spec,
    print_yolo_help,
    run_yolo_cli,
)

## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch GitHub Copilot CLI in the project context."
## @var SPEC
#  @brief Declarative YOLO CLI record bound to the `copilot` command token.
#  @satisfies DES-030, REQ-015, REQ-093
SPEC = get_yolo_spec("copilot")


def print_help(version: str) -> None:
    """@brief Print command-specific help for `copilot`.

    @details Delegates to the shared YOLO help renderer, which emits the
    executed option documentation, the accepted `--allow-all` alternative,
    and the alphabetical YOLO CLI registry.
    Time complexity O(n) over registered YOLO CLI record count.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-086, REQ-092, REQ-093
    """
    print_yolo_help(SPEC.command, version, DESCRIPTION)


def run(args: list[str]) -> int:
    """@brief Launch Copilot CLI in YOLO mode after executable validation.

    @details Delegates to the shared YOLO runner executing
    `copilot --yolo` plus pass-through args through blocking subprocess run
    with inherited stdio. Time complexity O(n) over forwarded argument count.
    @param args {list[str]} Additional CLI args forwarded to Copilot.
    @return {int} Child process return code.
    @satisfies REQ-015, REQ-055, REQ-056, REQ-064
    """
    return run_yolo_cli(SPEC.command, args)
