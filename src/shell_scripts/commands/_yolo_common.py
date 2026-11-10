#!/usr/bin/env python3
"""@brief Shared registry-based launcher for YOLO-mode external AI CLIs.

@details Defines the declarative `YoloCliSpec` registry plus the shared inline
help renderer and subprocess runner consumed by thin YOLO command modules.
Adding a new YOLO CLI requires exactly one `YoloCliSpec` record plus one thin
command module exposing `DESCRIPTION`, `print_help(version)`, and `run(args)`.
@satisfies DES-030, DES-031, REQ-055, REQ-056, REQ-064
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from shell_scripts.utils import require_commands

## @var PROGRAM
#  @brief Base CLI program name used in help output.
#  @details Constant identifier for usage-line rendering in command help.
PROGRAM = "shellscripts"


@dataclass(frozen=True)
class YoloCliSpec:
    """@brief Declarative definition of one YOLO-mode external AI CLI.

    @details Immutable registry record; a command module becomes a YOLO
    launcher by binding exactly one instance of this record.
    @satisfies DES-030
    """

    ## @var command
    #  @brief Dispatcher command token exposed by the CLI registry.
    command: str
    ## @var executable
    #  @brief External executable token resolved and validated before launch.
    executable: str
    ## @var option
    #  @brief YOLO-mode option inserted immediately after the executable.
    option: str
    ## @var note
    #  @brief Behavioral note rendered in inline help for `option`.
    note: str
    ## @var alternative
    #  @brief Documented-but-not-executed alternative option; empty when none.
    alternative: str = ""
    ## @var alternative_note
    #  @brief Behavioral note rendered in inline help for `alternative`.
    alternative_note: str = ""


## @var YOLO_CLI_REGISTRY
#  @brief Alphabetically ordered registry of YOLO-mode AI CLI definitions.
#  @details Rendered verbatim in every YOLO command inline help in this order;
#  appending one record extends the registry and every help surface.
#  @satisfies DES-030, REQ-086
YOLO_CLI_REGISTRY: tuple[YoloCliSpec, ...] = (
    YoloCliSpec(
        command="agy",
        executable="agy",
        option="--dangerously-skip-permissions",
        note="Official Antigravity flag used instead of --yolo.",
    ),
    YoloCliSpec(
        command="claude",
        executable="claude",
        option="--dangerously-skip-permissions",
        note=(
            "Ignores all approval, policy, and rule prompts"
            " for the entire session."
        ),
    ),
    YoloCliSpec(
        command="codex",
        executable="codex",
        option="--yolo",
        note=(
            "Skips confirmation prompts and entirely disables"
            " the security sandbox."
        ),
    ),
    YoloCliSpec(
        command="copilot",
        executable="copilot",
        option="--yolo",
        note="Skips confirmation prompts for the entire session.",
        alternative="--allow-all",
        alternative_note=(
            "Accepted alternative granting access to all paths and tools."
        ),
    ),
    YoloCliSpec(
        command="opencode",
        executable="opencode",
        option="--auto",
        note=(
            "Approves every request that is not explicitly denied; "
            "no formal --yolo flag exists."
        ),
    ),
)

## @var YOLO_CLI_INDEX
#  @brief O(1) command-token lookup index over `YOLO_CLI_REGISTRY`.
#  @satisfies DES-030
YOLO_CLI_INDEX: dict[str, YoloCliSpec] = {
    spec.command: spec for spec in YOLO_CLI_REGISTRY
}


def get_yolo_spec(command: str) -> YoloCliSpec:
    """@brief Resolve the declarative YOLO CLI record for one command token.

    @details Performs O(1) dictionary lookup on `YOLO_CLI_INDEX`.
    Time complexity O(1).
    @param command {str} Dispatcher command token (for example `codex`).
    @return {YoloCliSpec} Registry record bound to the command token.
    @throws {KeyError} If the command token is not registered.
    @satisfies DES-030
    """
    return YOLO_CLI_INDEX[command]


def print_yolo_help(command: str, version: str, description: str) -> None:
    """@brief Render YOLO command help documenting the full YOLO CLI registry.

    @details Emits the command description, usage line, executed YOLO option
    with its behavioral note, optional documented alternative option, and the
    complete registry listing with every executed option and note in ascending
    alphabetical command order; does not mutate process state.
    Time complexity O(n) over registered YOLO CLI record count.
    @param command {str} Dispatcher command token whose help is rendered.
    @param version {str} CLI version string propagated by dispatcher.
    @param description {str} One-line command description for the help header.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-086, REQ-092, REQ-093
    """
    spec = get_yolo_spec(command)
    print(description)
    print(f"Usage: {PROGRAM} {spec.command} [args...] ({version})")
    print()
    print(f"{spec.command} YOLO mode:")
    print(f"  Executed command: {spec.executable} {spec.option} [args...]")
    print(f"  {spec.option}  - {spec.note}")
    if spec.alternative:
        print(
            f"  {spec.alternative}  - {spec.alternative_note}"
            " (accepted alternative; never appended automatically)."
        )
    print("  --help  - Show this help message.")
    print()
    print("Registered YOLO CLIs (alphabetical order):")
    for entry in YOLO_CLI_REGISTRY:
        print(f"  {entry.command:<9} {entry.executable} {entry.option}")
        print(f"      {entry.note}")
        if entry.alternative:
            print(
                f"      Alternative: {entry.alternative}"
                f" - {entry.alternative_note}"
            )


def run_yolo_cli(command: str, args: list[str]) -> int:
    """@brief Launch one registered YOLO CLI after executable validation.

    @details Resolves the registry record, validates executable availability
    for the record executable, builds the command vector
    `[resolved_executable, option] + args`, then executes it through blocking
    `subprocess.run` with inherited stdio. Performs no Git repository root
    validation and emits no project-root error output. Time complexity O(n)
    over forwarded argument count.
    @param command {str} Registered dispatcher command token.
    @param args {list[str]} Additional CLI args forwarded to the external CLI.
    @return {int} Child process return code.
    @throws {KeyError} If the command token is not registered.
    @satisfies REQ-014, REQ-015, REQ-017, REQ-018, REQ-085,
        REQ-055, REQ-056, REQ-064
    """
    spec = get_yolo_spec(command)
    cmd = [spec.executable, spec.option] + args
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
