#!/usr/bin/env python3
import sys

from shell_scripts.commands._dc_common import dispatch

PROGRAM = "shellscripts"
DESCRIPTION = "File viewer dispatcher by MIME type for Double Commander."

CATEGORY_CMDS = {
    "image":    ["sushi"],
    "pdf":      ["sushi"],
    "text":     ["sushi"],
    "code":     ["sushi"],
    "html":     ["sushi"],
    "markdown": ["typora"],
}
FALLBACK = ["sushi"]


def print_help(version):
    print(f"Usage: {PROGRAM} double-commander-viewer <file> [args...] ({version})")
    print()
    print("double-commander-viewer options:")
    print("  <file>   - File to view (required).")
    print("  Additional arguments are passed to the selected viewer.")
    print("  --help   - Show this help message.")


def run(args):
    if not args:
        print("Error: file argument required.", file=sys.stderr)
        print_help("")
        return 2
    return dispatch(CATEGORY_CMDS, FALLBACK, args[0], args[1:])
