#!/usr/bin/env python3
"""@brief MIME-based diff command wrapper.

@details Exposes the `diff` CLI command and delegates category-based executable
selection to shared `_dc_common.dispatch` logic.
@satisfies PRJ-003, DES-007, REQ-023, REQ-024
"""

import sys

from shell_scripts.commands._dc_common import dispatch

PROGRAM = "shellscripts"
DESCRIPTION = "File differ dispatcher by MIME type."

CATEGORY_CMDS = {
    "image":    ["bcompare"],
    "pdf":      ["bcompare"],
    "text":     ["bcompare"],
    "code":     ["bcompare"],
    "html":     ["bcompare"],
    "markdown": ["bcompare"],
}
FALLBACK = ["bcompare"]


def print_help(version):
    """@brief Render command help for `diff`.

    @details Prints usage, required file argument semantics, and argument
    forwarding contract for the selected external diff executable.
    @param version {str} Version string appended in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """
    print(f"Usage: {PROGRAM} diff <file> [args...] ({version})")
    print()
    print("diff options:")
    print("  <file>   - File to diff (required).")
    print("  Additional arguments are passed to the selected diff tool.")
    print("  --help   - Show this help message.")


def run(args):
    """@brief Execute MIME-routed diff dispatch.

    @details Validates that a file argument exists; on missing argument prints
    error plus help and returns status code `2`; otherwise dispatches by file
    category through shared `_dc_common`.
    @param args {list[str]} CLI args where `args[0]` is file path.
    @return {int} Return code `2` on missing file; otherwise delegated dispatch result.
    @satisfies REQ-023, REQ-024
    """
    if not args:
        print("Error: file argument required.", file=sys.stderr)
        print_help("")
        return 2
    return dispatch(CATEGORY_CMDS, FALLBACK, args[0], args[1:])
