#!/usr/bin/env python3
"""@brief Google Chrome remote-debugging launcher.

@details Python port of the legacy `bin/chrome-debug.sh` script. Spawns
Google Chrome detached from the terminal session with the fixed remote
debugging port `9222` and the default Chrome user-data directory, with both
output streams suppressed, so debugging clients can attach to
`http://127.0.0.1:9222`.
@satisfies PRJ-008, DES-069, REQ-169, REQ-170
"""
from pathlib import Path
import subprocess

from shell_scripts.utils import print_info, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Launch Google Chrome with remote debugging enabled."

## @var DEBUG_PORT
#  @brief Fixed Chrome remote-debugging TCP port.
#  @details Passed to Chrome as `--remote-debugging-port` and rendered in the
#  final attach URL.
#  @satisfies REQ-169
DEBUG_PORT = 9222

## @var USER_DATA_SUBDIR
#  @brief Home-relative Chrome user-data directory path.
#  @details Resolved against `Path.home()` at launch time, matching the
#  legacy script `$HOME/.config/google-chrome` value.
#  @satisfies REQ-169
USER_DATA_SUBDIR = Path(".config") / "google-chrome"


def print_help(version):
    """@brief Print command-specific help text.

    @details Renders usage line, option list, and behavioral summary in
    English, following the shared command help layout.
    @param version {str} Current CLI version token rendered in the usage line.
    @return {None} Writes to stdout.
    @satisfies PRJ-002, REQ-169
    """
    print(f"Usage: {PROGRAM} chrome-debug ({version})")
    print()
    print("chrome-debug options:")
    print("  --help  - Show this help message.")
    print()
    print("Starts Google Chrome detached from the terminal with remote debugging")
    print(f"enabled on port {DEBUG_PORT}, using the default user data directory.")
    print(f"A CLI can then connect to http://127.0.0.1:{DEBUG_PORT}")


def run(args):
    """@brief Spawn the detached Chrome remote-debugging instance.

    @details Validates the `google-chrome` executable, resolves the user-data
    directory from `Path.home()`, prints English progress messages, spawns
    `google-chrome --remote-debugging-port=<port> --user-data-dir=<dir>` via
    `subprocess.Popen` with all stdio streams set to `DEVNULL` and
    `start_new_session=True` (equivalent to `nohup ... &`), and returns
    without waiting so the browser outlives the CLI process.
    @param args {list[str]} Unused command arguments.
    @return {int} `0` after spawning the detached browser process.
    @throws {SystemExit} Exit code `1` via `require_commands` when
      `google-chrome` is not executable.
    @satisfies REQ-169, REQ-170, CTN-003, REQ-056
    """
    require_commands("google-chrome")

    user_data_dir = Path.home() / USER_DATA_SUBDIR
    print_info(f"Launching Google Chrome in debug mode on port {DEBUG_PORT}...")
    print_info(f"Using user data directory: {user_data_dir}")

    subprocess.Popen(
        [
            "google-chrome",
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={user_data_dir}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    print_info(f"Browser started. A CLI can connect to http://127.0.0.1:{DEBUG_PORT}")
    return 0
