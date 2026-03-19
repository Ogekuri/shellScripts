#!/usr/bin/env python3
import sys

from shell_scripts.commands._dc_common import dispatch

PROGRAM = "shellscripts"
DESCRIPTION = "File editor dispatcher by MIME type for Double Commander."

CATEGORY_CMDS = {
    "image":    ["gimp"],
    "pdf":      ["okular"],
    "text":     ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
    "code":     ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
    "html":     ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
    "markdown": ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
}
FALLBACK = ["/opt/sublime_text/sublime_text", "-n", "-wait"]


def print_help(version):
    print(f"Usage: {PROGRAM} double-commander-editor <file> [args...] ({version})")
    print()
    print("double-commander-editor options:")
    print("  <file>   - File to edit (required).")
    print("  Additional arguments are passed to the selected editor.")
    print("  --help   - Show this help message.")


def run(args):
    if not args:
        print("Error: file argument required.", file=sys.stderr)
        print_help("")
        return 2
    return dispatch(CATEGORY_CMDS, FALLBACK, args[0], args[1:])
