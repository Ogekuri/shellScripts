#!/usr/bin/env python3
import sys
import subprocess

from shell_scripts import __version__
from shell_scripts.version_check import check_for_updates
from shell_scripts.commands import get_command, get_all_commands
from shell_scripts.utils import is_linux, print_error

PROGRAM = "shellscripts"
OWNER = "Ogekuri"
REPOSITORY = "shellScripts"


def print_help(command_name=None):
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
    print(f"  --upgrade    - Reinstall {PROGRAM} on Linux; print manual command elsewhere.")
    print(f"  --uninstall  - Uninstall {PROGRAM} on Linux; print manual command elsewhere.")
    print(f"  --ver        - Print the {PROGRAM} version.")
    print(f"  --version    - Print the {PROGRAM} version.")
    print(f"  --help       - Print the full help screen or the help text of a specific command.")
    print()
    print("Commands:")
    commands = get_all_commands()
    max_name = max(len(n) for n in commands) if commands else 10
    for name, desc in commands.items():
        print(f"  {name:<{max_name}}  - {desc}")


def do_upgrade():
    install_cmd = (
        f"uv tool install {PROGRAM} --force "
        f"--from git+https://github.com/{OWNER}/{REPOSITORY}.git"
    )
    if is_linux():
        print(f"Upgrading {PROGRAM}...")
        result = subprocess.run(install_cmd, shell=True)
        return result.returncode
    else:
        print(f"{PROGRAM} automatic upgrade is only supported on Linux.")
        print(f"Run this command manually:")
        print(f"  {install_cmd}")
        return 0


def do_uninstall():
    uninstall_cmd = f"uv tool uninstall {PROGRAM}"
    if is_linux():
        print(f"Uninstalling {PROGRAM}...")
        result = subprocess.run(uninstall_cmd, shell=True)
        return result.returncode
    else:
        print(f"{PROGRAM} automatic uninstall is only supported on Linux.")
        print(f"Run this command manually:")
        print(f"  {uninstall_cmd}")
        return 0


def main():
    check_for_updates(__version__)

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
