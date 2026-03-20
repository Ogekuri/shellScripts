#!/usr/bin/env python3
"""@brief Main shellscripts CLI dispatcher and management operation handler.

@details Provides global help rendering, management command execution
(`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`), runtime
configuration bootstrap, and subcommand delegation to lazily imported modules.
@satisfies PRJ-001, PRJ-002, PRJ-003, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046
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
from shell_scripts.commands import get_command, get_all_commands
from shell_scripts.utils import detect_runtime_os, is_linux, print_error, print_info

PROGRAM = "shellscripts"


def print_help(command_name=None):
    """@brief Print global or command-specific help text.

    @details Renders command module help for known command names; otherwise exits
    with explicit unknown-command error. Global help includes management options
    and all command descriptions sorted by registry key.
    @param command_name {str|None} Optional command token for scoped help.
    @return {None} Writes to stdout/stderr; may terminate process on invalid command.
    @throws {SystemExit} Raised when unknown command name is requested.
    @satisfies PRJ-002, REQ-001, REQ-002
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
    print("Commands:")
    commands = get_all_commands()
    max_name = max(len(n) for n in commands) if commands else 10
    for name, desc in commands.items():
        print(f"  {name:<{max_name}}  - {desc}")


def do_upgrade():
    """@brief Execute Linux-only upgrade command resolved from runtime config.

    @details Reads management command string from runtime config key
    `management.upgrade`, executes it on Linux via shell invocation, and prints
    manual fallback command on non-Linux systems.
    @return {int} Subprocess return code on Linux; `0` on non-Linux fallback.
    @satisfies REQ-004, REQ-045
    """

    install_cmd = get_management_command("upgrade")
    if is_linux():
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
    @satisfies REQ-005, REQ-045
    """

    uninstall_cmd = get_management_command("uninstall")
    if is_linux():
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
    print_info(f"Default runtime config written to: {target}")
    return 0


def main():
    """@brief Entrypoint for shellscripts argument dispatch.

    @details Performs runtime OS detection, update check, runtime configuration
    load, and argument dispatch through management flags and subcommands.
    @return {int} Process-compatible return code for caller (`sys.exit`).
    @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047
    """

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
