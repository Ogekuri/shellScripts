#!/usr/bin/env python3
"""@brief pi.dev CLI launcher in project context.

@details Ensures project-root prerequisite and executable availability before
blocking subprocess invocation of `pi`. For invocations without any `--tools`
argument token, appends default tools parameter required by project contract.
@satisfies REQ-055, REQ-056, REQ-064, REQ-068, REQ-069
"""

import subprocess

from shell_scripts.utils import require_project_root, require_commands

## @var PROGRAM
#  @brief Base CLI program name used in help output.
#  @details Constant identifier for usage-line rendering in command help.
PROGRAM = "shellscripts"

## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch pi.dev CLI in the project context."

## @var _DEFAULT_TOOLS_VALUE
#  @brief Default `--tools` payload for `pi` command invocations.
#  @details Applied only when no `--tools` option token is present in forwarded
#  arguments.
#  @satisfies REQ-068, REQ-069
_DEFAULT_TOOLS_VALUE = "read,bash,edit,write,grep,find,ls"


def print_help(version):
    """@brief Print command-specific help for `pi`.

    @details Emits usage and pass-through argument behavior for deterministic
    terminal rendering; documents default `--tools` append semantics and
    override behavior when `--tools` is explicitly provided.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-068, REQ-069
    """

    print(f"Usage: {PROGRAM} pi [args...] ({version})")
    print()
    print("pi options:")
    print("  All arguments are passed through to the pi.dev CLI.")
    print(f"  If --tools is absent, appends default: --tools {_DEFAULT_TOOLS_VALUE}.")
    print("  If --tools is provided, passed value overrides defaults.")
    print("  --help  - Show this help message.")


def _has_tools_option(args):
    """@brief Detect whether forwarded args include a `--tools` option token.

    @details Detects both tokenized forms `--tools <value>` and
    single-token form `--tools=<value>` using exact prefix matching on each
    argument element. Time complexity O(n), where n is the argument count.
    @param args {list[str]} Forwarded CLI args for `pi` launcher.
    @return {bool} `True` when any argument token provides `--tools`; `False`
    otherwise.
    @satisfies REQ-068, REQ-069
    """

    return any(arg == "--tools" or arg.startswith("--tools=") for arg in args)


def run(args):
    """@brief Launch pi.dev CLI after external executable validation.

    @details Resolves project root, checks executable availability for `pi`,
    forwards all CLI arguments unchanged, and appends default tools option only
    when no `--tools` token exists in input args.
    @param args {list[str]} Additional CLI args forwarded to pi.dev.
    @return {int} Child process return code.
    @satisfies REQ-055, REQ-056, REQ-064, REQ-068, REQ-069
    """

    require_project_root()
    cmd = ["pi"] + args
    if not _has_tools_option(args):
        cmd.extend(["--tools", _DEFAULT_TOOLS_VALUE])
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
