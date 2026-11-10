#!/usr/bin/env python3
"""@brief Main shellscripts CLI dispatcher and management operation handler.

@details Provides global help rendering, management command execution
(`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`,
`--develop`/`--dev` upgrade selector, `--force` forced-reinstall selector,
configuration CLI flags `--print-raw`, `--print`, `--params`, `--get`,
`--set`, `--unset`),
runtime configuration bootstrap, and subcommand delegation to lazily imported
modules.
@satisfies PRJ-001, PRJ-002, PRJ-003, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-056, REQ-064, REQ-065, REQ-066, REQ-068, REQ-069, REQ-075, REQ-076, REQ-077, REQ-078, REQ-087, REQ-088, REQ-089, REQ-090, REQ-091, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104, REQ-105, REQ-106, REQ-107, REQ-108, REQ-109, DES-032, DES-033, DES-034, DES-035
"""

import sys
import subprocess

from shell_scripts import __version__
from shell_scripts.config import (
    get_management_command,
    load_runtime_config,
    write_default_runtime_config,
)
from shell_scripts.version_check import (
    check_for_updates,
    fetch_github_latest_release,
    format_version_report_line,
    print_remote_latest_versions,
)
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

## @var FORCED_REINSTALL_OPTIONS
#  @brief Option suffix appended to upgrade commands when `--force` is active.
#  @details Standard forced-reinstall options for `uv tool install`: replace
#  the installed tool entry, reinstall the package, and refresh cached remote
#  metadata so the upgrade performs a full re-download and reinstallation.
#  @satisfies REQ-088, REQ-089
FORCED_REINSTALL_OPTIONS = "--force --reinstall --refresh"

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
            "agy",
            "claude",
            "codex",
            "copilot",
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
    @satisfies PRJ-002, DES-014, REQ-001, REQ-002, REQ-066, REQ-068, REQ-069
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
        "  --dev        - With --upgrade: upgrade from the latest GitHub release tag"
    )
    print("                 instead of PyPI (alias: --develop).")
    print(
        "  --force      - With --upgrade: force download and complete reinstallation"
    )
    print("                 (appends --force --reinstall --refresh).")
    print(
        f"  --uninstall  - Uninstall {PROGRAM} on Linux; print manual command elsewhere."
    )
    print("  --write-config - Write default runtime config to user config directory.")
    print("  --print-raw  - Print the raw runtime config file content from disk.")
    print("  --print      - Print the active configuration as an options tree.")
    print("  --params     - Print configurable parameters with descriptions.")
    print("  --get <path> - Read one configuration value; path parts separated by ':'.")
    print("  --set <path> <value> - Set one configuration value; path separated by ':'.")
    print("  --unset <path> - Remove one configuration override; path separated by ':'.")
    print(
        f"  --ver        - Print the {PROGRAM} version plus latest PyPI and GitHub versions."
    )
    print(
        f"  --version    - Print the {PROGRAM} version plus latest PyPI and GitHub versions."
    )
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


def _build_develop_upgrade_command(latest_tag: str) -> str:
    """@brief Compose the develop upgrade command for one GitHub release tag.

    @details Resolves the `management.upgrade_develop` runtime-config template,
    substitutes the `{tag}` placeholder with the supplied tag, and returns the
    shell command that installs the package from the GitHub tag archive.
    Complexity O(n) over template length.
    @param latest_tag {str} GitHub release tag token preserving its `v` prefix.
    @return {str} Fully substituted shell upgrade command.
    @satisfies REQ-076, DES-019
    """

    template = get_management_command("upgrade_develop")
    return template.replace("{tag}", latest_tag)


def do_upgrade(develop: bool = False, force: bool = False) -> int:
    """@brief Execute Linux-only upgrade command resolved from runtime config.

    @details Reads management command string from runtime config key
    `management.upgrade` (PyPI default) or, when `develop` is set, resolves
    the latest GitHub release tag and composes the tag-pinned upgrade command;
    appends ` --force --reinstall --refresh` to the resolved command when
    `force` is set; executes the composed command on Linux via shell
    invocation and prints the manual fallback command on non-Linux systems.
    Complexity O(n) over the composed command string length.
    @param develop {bool} Select upgrade from the latest GitHub release tag.
    @param force {bool} Append forced-reinstall options to the upgrade command.
    @return {int} `1` when develop tag resolution fails; subprocess return code
      on Linux; `0` on non-Linux fallback.
    @satisfies REQ-004, REQ-076, REQ-078, REQ-087, REQ-088, REQ-089, REQ-045, REQ-056
    """

    if develop:
        try:
            latest_tag = fetch_github_latest_release(__version__)
        except Exception as error:
            print_error(f"GitHub latest release resolution failed: {error}.")
            return 1
        install_cmd = _build_develop_upgrade_command(latest_tag)
    else:
        install_cmd = get_management_command("upgrade")
    if force:
        install_cmd = f"{install_cmd} {FORCED_REINSTALL_OPTIONS}"
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
    load, and argument dispatch through management flags (`--version` prints
    the aligned three-line report with installed plus PyPI/GitHub latest
    versions; `--upgrade` upgrades from PyPI
    or, with `--develop`/`--dev`, from the latest GitHub release tag; `--force`
    appends forced-reinstall options to the selected upgrade command; bare
    `--develop`/`--dev`/`--force` selectors are rejected) and subcommands,
    then restores terminal raw/cbreak and disables legacy+xterm
    mouse-tracking modes (`?9l`, `?1000l`, `?1001l`, `?1002l`, `?1003l`,
    `?1004l`, `?1005l`, `?1006l`, `?1007l`, `?1015l`, `?1016l`) before exit.
    @return {int} Process-compatible return code for caller (`sys.exit`).
    @satisfies PRJ-001, REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-064, REQ-065, REQ-066, REQ-068, REQ-069, REQ-075, REQ-076, REQ-077, REQ-078, REQ-087, REQ-088, REQ-089, REQ-090, REQ-091, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104, REQ-105, REQ-106, REQ-107, REQ-108, REQ-109
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
            print(format_version_report_line("Current Installed", __version__))
            print_remote_latest_versions(__version__)
            return 0

        if first_arg == "--upgrade":
            develop = any(arg in ("--develop", "--dev") for arg in args[1:])
            force = "--force" in args[1:]
            return do_upgrade(develop=develop, force=force)

        if first_arg in ("--develop", "--dev"):
            print_error("--develop/--dev must be used together with --upgrade.")
            return 1

        if first_arg == "--force":
            print_error("--force must be used together with --upgrade.")
            return 1

        if first_arg == "--uninstall":
            return do_uninstall()

        if first_arg == "--write-config":
            return do_write_config()

        if first_arg in (
            "--print-raw",
            "--print",
            "--params",
            "--get",
            "--set",
            "--unset",
        ):
            from shell_scripts import config_cli

            if first_arg == "--print-raw":
                return config_cli.do_print_raw()
            if first_arg == "--print":
                return config_cli.do_print()
            if first_arg == "--params":
                return config_cli.do_params()
            if first_arg == "--get":
                return config_cli.do_get(args[1] if len(args) > 1 else None)
            if first_arg == "--set":
                return config_cli.do_set(
                    args[1] if len(args) > 1 else None,
                    args[2] if len(args) > 2 else None,
                )
            return config_cli.do_unset(args[1] if len(args) > 1 else None)

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
