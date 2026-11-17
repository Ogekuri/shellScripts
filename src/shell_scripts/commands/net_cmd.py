#!/usr/bin/env python3
"""@brief Network status and VLAN management command.

@details Python port of the legacy `bin/network.sh` script. The `status`
subcommand prints boxed English section headers followed by nmcli,
resolvectl, ip route, and journalctl output; the `vlan` subcommand activates
or deactivates `vlan<id>` connections through `sudo nmcli` and prints the
assigned addresses after successful activation.
@satisfies PRJ-008, DES-069, REQ-171, REQ-172, REQ-173
"""
import re
import subprocess

from shell_scripts.utils import print_error, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Print network status and manage VLAN connections."

## @var GREEN
#  @brief ANSI bright-green SGR prefix for status box borders.
#  @details Replicates the legacy script color `\e[1;32m`.
#  @satisfies REQ-171
GREEN = "\x1b[1;32m"

## @var BLUE
#  @brief ANSI bright-blue SGR prefix for the DNS section box.
#  @details Replicates the legacy script color `\e[1;34m`.
#  @satisfies REQ-171
BLUE = "\x1b[1;34m"

## @var MAGENTA
#  @brief ANSI bright-magenta SGR prefix for the routing section box.
#  @details Replicates the legacy script color `\e[1;35m`.
#  @satisfies REQ-171
MAGENTA = "\x1b[1;35m"

## @var LIGHT_GRAY
#  @brief ANSI light-gray SGR prefix for the journal section box.
#  @details Replicates the legacy script color `\e[0;37m`.
#  @satisfies REQ-171
LIGHT_GRAY = "\x1b[0;37m"

## @var WHITE
#  @brief ANSI bright-white SGR prefix for box titles and usage header.
#  @details Replicates the legacy script color `\e[1;37m`.
#  @satisfies REQ-171
WHITE = "\x1b[1;37m"

## @var RESET
#  @brief ANSI SGR reset suffix restoring default attributes.
#  @details Replicates the legacy script color `\e[0m`.
#  @satisfies REQ-171
RESET = "\x1b[0m"

## @var RED
#  @brief ANSI bright-red SGR prefix for error lines.
#  @details Replicates the legacy script color `\e[1;31m`.
#  @satisfies REQ-173
RED = "\x1b[1;31m"

## @var YELLOW
#  @brief ANSI bright-yellow SGR prefix for deactivation notice lines.
#  @details Replicates the legacy script color `\e[1;33m`.
#  @satisfies REQ-172
YELLOW = "\x1b[1;33m"

## @var BOX_WIDTH
#  @brief Fixed inner width in dash glyphs for every section box.
#  @details Replicates the legacy script width `70`; title centering is
#  computed against this value.
#  @satisfies REQ-171
BOX_WIDTH = 70

## @var JOURNAL_TAIL_LINES
#  @brief Number of trailing journal lines printed by the status report.
#  @details Replicates the legacy `journalctl ... | tail -n 15` behavior.
#  @satisfies REQ-171
JOURNAL_TAIL_LINES = 15

## @var VLAN_ADDRESS_AFTER_LINES
#  @brief Context lines printed after each matching VLAN address line.
#  @details Replicates the legacy `grep -E ... -A 2` behavior.
#  @satisfies REQ-172
VLAN_ADDRESS_AFTER_LINES = 2


def print_box(title, color):
    """@brief Print one centered-title ASCII box header.

    @details Replicates the legacy `print_box` layout: a leading blank line,
    `┌` plus 70 `─` glyphs plus `┐` borders in `color`, a title row with the
    title wrapped in `WHITE` and padded to `BOX_WIDTH` using the split
    `padding = (BOX_WIDTH - len(title) - 2) // 2` left and the remainder
    right, and a closing `└...┘` border row.
    @param title {str} ASCII section title rendered inside the box.
    @param color {str} ANSI SGR prefix applied to the border glyphs.
    @return {None} Writes to stdout.
    @satisfies REQ-171
    """
    padding = (BOX_WIDTH - len(title) - 2) // 2
    right_padding = BOX_WIDTH - len(title) - 2 - padding
    pad_str = " " * padding
    right_pad_str = " " * right_padding
    top_bottom_line = "─" * BOX_WIDTH

    print()
    print(f"{color}┌{top_bottom_line}┐{RESET}")
    print(f"{color}│{RESET}{pad_str}{WHITE} {title} {RESET}{right_pad_str}{color}│{RESET}")
    print(f"{color}└{top_bottom_line}┘{RESET}")


def cmd_status():
    """@brief Print the full network status report.

    @details Emits boxed English section headers followed by, in order:
    `nmcli device status`, `nmcli -f NAME,TYPE,AUTOCONNECT,DEVICE connection
    show`, `resolvectl status`, `ip route`, and the last
    `JOURNAL_TAIL_LINES` lines of `journalctl -b -u networking.service
    --no-pager` captured output. Each external tool is validated immediately
    before its section and a missing tool terminates with exit code `1`.
    @return {int} `0` after printing every section; `1` when a required
      executable is unavailable.
    @throws {SystemExit} Exit code `1` via `require_commands` when a required
      executable is not executable.
    @satisfies REQ-171, REQ-056
    """
    print_box("Network Device Status", GREEN)
    require_commands("nmcli")
    subprocess.run(["nmcli", "device", "status"])

    print_box("Network Connections (Autoconnect)", GREEN)
    subprocess.run(["nmcli", "-f", "NAME,TYPE,AUTOCONNECT,DEVICE", "connection", "show"])

    print_box("DNS Resolution Status (resolvectl)", BLUE)
    require_commands("resolvectl")
    subprocess.run(["resolvectl", "status"])

    print_box("Routing Table (ip route)", MAGENTA)
    require_commands("ip")
    subprocess.run(["ip", "route"])

    print_box("Network Service Log (journalctl)", LIGHT_GRAY)
    require_commands("journalctl")
    result = subprocess.run(
        ["journalctl", "-b", "-u", "networking.service", "--no-pager"],
        capture_output=True, text=True,
    )
    lines = result.stdout.splitlines()
    for line in lines[-JOURNAL_TAIL_LINES:]:
        print(line)
    return 0


def _print_vlan_addresses(vlan_id):
    """@brief Print current addresses of one VLAN, mirroring `grep -A 2`.

    @details Runs `ip addr show` with captured stdout, selects every line
    matching `vlan<vlan_id>` or `enp.*\.<vlan_id>`, and prints each match
    plus the following `VLAN_ADDRESS_AFTER_LINES` context lines without
    duplicating overlapping context windows.
    @param vlan_id {str} Numeric VLAN identifier used in match patterns.
    @return {None} Writes matching address blocks to stdout.
    @satisfies REQ-172
    """
    result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    pattern = re.compile(rf"vlan{vlan_id}|enp.*\.{vlan_id}")
    printed_until = -1
    for index, line in enumerate(lines):
        if pattern.search(line) and index > printed_until:
            for context_line in lines[index:index + VLAN_ADDRESS_AFTER_LINES + 1]:
                print(context_line)
            printed_until = index + VLAN_ADDRESS_AFTER_LINES


def cmd_vlan(vlan_id, action):
    """@brief Activate or deactivate one VLAN connection.

    @details Rejects missing parameters and unknown actions with the English
    usage text and exit code `1`; otherwise runs `sudo nmcli connection
    up|down vlan<vlan_id>` with inherited stdio and blocking wait, and after
    a successful activation prints the current VLAN address blocks. The
    return code propagates the `sudo nmcli` result.
    @param vlan_id {str|None} VLAN identifier token (e.g. `50`).
    @param action {str|None} Requested action; only `up` and `down` are valid.
    @return {int} `0` on success; the `sudo nmcli` return code on activation
      or deactivation failure; `1` on parameter or action validation failure.
    @satisfies REQ-172, REQ-173
    """
    if not vlan_id or not action:
        print_error("Error: missing parameters.")
        print(f"Correct usage: {PROGRAM} net vlan <id> up   (e.g. {PROGRAM} net vlan 50 up)")
        print(f"              {PROGRAM} net vlan <id> down (e.g. {PROGRAM} net vlan 50 down)")
        return 1

    vlan_name = f"vlan{vlan_id}"

    if action == "up":
        print()
        print(f"{GREEN}Activating connection {vlan_name}...{RESET}")
        result = subprocess.run(["sudo", "nmcli", "connection", "up", vlan_name])
        if result.returncode == 0:
            print()
            print(f"{BLUE}Current IP addresses for VLAN {vlan_id}:{RESET}")
            _print_vlan_addresses(vlan_id)
        return result.returncode

    if action == "down":
        print()
        print(f"{YELLOW}Deactivating connection {vlan_name}...{RESET}")
        result = subprocess.run(["sudo", "nmcli", "connection", "down", vlan_name])
        return result.returncode

    print(f"{RED}Error: invalid action '{action}'.{RESET} Use 'up' or 'down'.")
    return 1


def print_usage():
    """@brief Print the English command usage block.

    @details Renders the bright-white script title, the available-command
    list, and no return value; callers combine it with return code `1`.
    @return {None} Writes to stdout.
    @satisfies REQ-173
    """
    print(f"{WHITE}Network Management Script{RESET}")
    print("Available commands:")
    print(f"  {PROGRAM} net status              - Show the full network status")
    print(f"  {PROGRAM} net vlan <id> up        - Activate a specific VLAN")
    print(f"  {PROGRAM} net vlan <id> down      - Deactivate a specific VLAN")


def print_help(version):
    """@brief Print command-specific help text.

    @details Renders usage line, option list, and subcommand summary in
    English, following the shared command help layout.
    @param version {str} Current CLI version token rendered in the usage line.
    @return {None} Writes to stdout.
    @satisfies PRJ-002, REQ-171
    """
    print(f"Usage: {PROGRAM} net ({version})")
    print()
    print("net options:")
    print("  --help  - Show this help message.")
    print()
    print("Subcommands:")
    print("  status              - Show the full network status")
    print("  vlan <id> up        - Activate a specific VLAN")
    print("  vlan <id> down      - Deactivate a specific VLAN")


def run(args):
    """@brief Route `net` subcommands.

    @details Dispatches `status` to `cmd_status` and `vlan` with two
    positional arguments to `cmd_vlan`; any missing, unknown, or malformed
    subcommand prints the English usage block and returns exit code `1`.
    @param args {list[str]} Command arguments (without the command token).
    @return {int} `0` on successful subcommand completion; `1` on usage
      errors or propagated VLAN command failure.
    @satisfies REQ-171, REQ-172, REQ-173
    """
    if not args:
        print_usage()
        return 1

    subcommand = args[0]
    if subcommand == "status":
        return cmd_status()
    if subcommand == "vlan":
        return cmd_vlan(
            args[1] if len(args) > 1 else None,
            args[2] if len(args) > 2 else None,
        )

    print_usage()
    return 1
