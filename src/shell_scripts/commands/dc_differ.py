#!/usr/bin/env python3
import sys

from shell_scripts.commands._dc_common import dispatch

PROGRAM = "shellscripts"
DESCRIPTION = "File differ dispatcher by MIME type for Double Commander."

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
    print(f"Usage: {PROGRAM} double-commander-differ <file> [args...] ({version})")
    print()
    print("double-commander-differ options:")
    print("  <file>   - File to diff (required).")
    print("  Additional arguments are passed to the selected diff tool.")
    print("  --help   - Show this help message.")


def run(args):
    if not args:
        print("Error: file argument required.", file=sys.stderr)
        print_help("")
        return 2
    return dispatch(CATEGORY_CMDS, FALLBACK, args[0], args[1:])
