#!/usr/bin/env python3
"""@brief MIME-based edit command wrapper.

@details Exposes the `edit` CLI command and delegates category-based executable
selection to shared `_dc_common.dispatch` logic.
@satisfies PRJ-003, DES-007, REQ-023, REQ-024
"""

import sys

from shell_scripts.config import get_dispatch_profile
from shell_scripts.commands._dc_common import dispatch

PROGRAM = "shellscripts"
DESCRIPTION = "File editor dispatcher by MIME type."


def print_help(version):
    """@brief Render command help for `edit`.

    @details Prints usage, required file argument semantics, and argument
    forwarding contract for the selected external editor executable.
    @param version {str} Version string appended in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """
    print(f"Usage: {PROGRAM} edit <file> [args...] ({version})")
    print()
    print("edit options:")
    print("  <file>   - File to edit (required).")
    print("  Additional arguments are passed to the selected editor.")
    print("  --help   - Show this help message.")


def run(args):
    """@brief Execute MIME-routed edit dispatch.

    @details Validates that a file argument exists; on missing argument prints
    error plus help and returns status code `2`; otherwise resolves runtime
    dispatch profile and delegates by file category through shared `_dc_common`.
    @param args {list[str]} CLI args where `args[0]` is file path.
    @return {int} Return code `2` on missing file; otherwise delegated dispatch result.
    @satisfies REQ-023, REQ-024
    """
    if not args:
        print("Error: file argument required.", file=sys.stderr)
        print_help("")
        return 2
    category_cmds, fallback = get_dispatch_profile("edit")
    return dispatch(category_cmds, fallback, args[0], args[1:])
