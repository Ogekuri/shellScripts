#!/usr/bin/env python3
"""@brief Main shellscripts CLI dispatcher and management operation handler.

@details Provides global help rendering, management command execution
(`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`), runtime
configuration bootstrap, and subcommand delegation to lazily imported modules.
@satisfies PRJ-001, PRJ-002, PRJ-003, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-056, REQ-064, REQ-065, REQ-066
"""

import sys
import subprocess

from shell_scripts import __version__
from shell_scripts.config import (
    get_management_command,
    load_runtime_config,
    write_default_runtime_config,
)
from shell_scripts.version_check import check_for_updates
from shell_scripts.commands import get_command
from shell_scripts.utils import (
    capture_terminal_state,
    detect_runtime_os,
    is_linux,
    print_error,
    print_info,
    reset_terminal_state,
    require_shell_command_executables,
)

PROGRAM = "shellscripts"
## @var HELP_COMMAND_COLUMN_WIDTH
#  @brief Fixed command-name column width for grouped help rendering.
#  @details Forces deterministic spacing for all command rows across grouped
#  global help sections.
#  @satisfies REQ-066
HELP_COMMAND_COLUMN_WIDTH = 16

## @var HELP_SECTION_COMMANDS
#  @brief Ordered command groups for global help rendering.
#  @details Defines deterministic section order and command-token order used by
#  `print_help` when emitting grouped command help. Ordering is normative and
#  maps directly to REQ-066 output expectations.
#  @satisfies DES-014, REQ-066
HELP_SECTION_COMMANDS = (
    (
        "Edit/View Commands",
        (
            "edit",
            "view",
            "diff",
        ),
    ),
    (
        "PDF Commands",
        (
            "pdf-crop",
            "pdf-merge",
            "pdf-split-by-format",
            "pdf-split-by-toc",
            "pdf-tiler-090",
            "pdf-tiler-100",
            "pdf-toc-clean",
        ),
    ),
    (
        "AI Commands",
        (
            "ai-install",
            "claude",
            "codex",
            "copilot",
            "gemini",
            "kiro",
            "opencode",
        ),
    ),
    (
        "Develop Commands",
        (
            "req",
            "venv",
            "clean",
            "doxygen",
            "tests",
            "vscode",
            "vsinsider",
        ),
    ),
    (
        "Image Commands",
        (
            "dicom2jpg",
            "dicomviewer",
        ),
    ),
    (
        "Video Commands",
        (
            "video2h264",
            "video2h265",
        ),
    ),
    (
        "OS Commands",
        ("ubuntu-dark-theme",),
    ),
)


def print_help(command_name=None):
    """@brief Print global or command-specific help text.

    @details Renders command module help for known command names; otherwise exits
    with explicit unknown-command error. Global help includes management options
    and grouped command sections using deterministic section and command order,
    with descriptions sourced from each command module `DESCRIPTION` constant.
    @param command_name {str|None} Optional command token for scoped help.
    @return {None} Writes to stdout/stderr; may terminate process on invalid command.
    @throws {SystemExit} Raised when unknown command name is requested.
    @satisfies PRJ-002, DES-014, REQ-001, REQ-002, REQ-066
    """

    if command_name:
        cmd = get_command(command_name)
        if cmd:
            cmd.print_help(__version__)
        else:
            print_error(f"Unknown command: {command_name}")
            sys.exit(1)
        return

    print(f"Usage: {PROGRAM} [command] [options] ({__version__})")
    print()
    print("Management Commands:")
    print(
        f"  --upgrade    - Reinstall {PROGRAM} on Linux; print manual command elsewhere."
    )
    print(
        f"  --uninstall  - Uninstall {PROGRAM} on Linux; print manual command elsewhere."
    )
    print("  --write-config - Write default runtime config to user config directory.")
    print(f"  --ver        - Print the {PROGRAM} version.")
    print(f"  --version    - Print the {PROGRAM} version.")
    print(
        "  --help       - Print the full help screen or the help text of a specific command."
    )
    print()
    for section_name, command_names in HELP_SECTION_COMMANDS:
        print()
        print(section_name)
        for command_name in command_names:
            command_module = get_command(command_name)
            description = getattr(command_module, "DESCRIPTION", "")
            print(f"  {command_name:<{HELP_COMMAND_COLUMN_WIDTH}} - {description}")


def do_upgrade():
    """@brief Execute Linux-only upgrade command resolved from runtime config.

    @details Reads management command string from runtime config key
    `management.upgrade`, executes it on Linux via shell invocation, and prints
    manual fallback command on non-Linux systems.
    @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
    @satisfies REQ-004, REQ-045, REQ-056
    """

    install_cmd = get_management_command("upgrade")
    if is_linux():
        require_shell_command_executables(install_cmd)
        print(f"Upgrading {PROGRAM}...")
        result = subprocess.run(install_cmd, shell=True)
        return result.returncode
    else:
        print(f"{PROGRAM} automatic upgrade is only supported on Linux.")
        print("Run this command manually:")
        print(f"  {install_cmd}")
        return 0


def do_uninstall():
    """@brief Execute Linux-only uninstall command resolved from runtime config.

    @details Reads management command string from runtime config key
    `management.uninstall`, executes it on Linux via shell invocation, and
    prints manual fallback command on non-Linux systems.
    @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
    @satisfies REQ-005, REQ-045, REQ-056
    """

    uninstall_cmd = get_management_command("uninstall")
    if is_linux():
        require_shell_command_executables(uninstall_cmd)
        print(f"Uninstalling {PROGRAM}...")
        result = subprocess.run(uninstall_cmd, shell=True)
        return result.returncode
    else:
        print(f"{PROGRAM} automatic uninstall is only supported on Linux.")
        print("Run this command manually:")
        print(f"  {uninstall_cmd}")
        return 0


def do_write_config():
    """@brief Persist default runtime configuration file to disk.

    @details Writes canonical config JSON to
    `$HOME/.config/shellScripts/config.json` and logs destination path.
    @return {int} `0` on successful write.
    @throws {OSError} Propagated on filesystem write failure.
    @satisfies REQ-046
    """

    target = write_default_runtime_config()
    target_text = target.as_posix() if hasattr(target, "as_posix") else str(target)
    print_info(f"Default runtime config written to: {target_text}")
    return 0


def main():
    """@brief Entrypoint for shellscripts argument dispatch.

    @details Performs runtime OS detection, update check, runtime configuration
    load, and argument dispatch through management flags and subcommands, then
    restores terminal raw/cbreak and disables legacy+xterm mouse-tracking modes
    (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`, `?1004l`, `?1005l`,
    `?1006l`, `?1007l`, `?1015l`, `?1016l`) before exit.
    @return {int} Process-compatible return code for caller (`sys.exit`).
    @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-064, REQ-065, REQ-066
    """
    saved_tty = capture_terminal_state()
    try:
        detect_runtime_os()
        check_for_updates(__version__)
        load_runtime_config()

        args = sys.argv[1:]

        if not args:
            print_help()
            return 0

        first_arg = args[0]

        if first_arg in ("--version", "--ver"):
            print(__version__)
            return 0

        if first_arg == "--upgrade":
            return do_upgrade()

        if first_arg == "--uninstall":
            return do_uninstall()

        if first_arg == "--write-config":
            return do_write_config()

        if first_arg == "--help":
            if len(args) > 1:
                print_help(args[1])
            else:
                print_help()
            return 0

        cmd = get_command(first_arg)
        if cmd:
            cmd_args = args[1:]
            if "--help" in cmd_args:
                cmd.print_help(__version__)
                return 0
            return cmd.run(cmd_args) or 0

        print_error(f"Unknown command: {first_arg}")
        print()
        print_help()
        return 1
    finally:
        reset_terminal_state(saved_tty)
