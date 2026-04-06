#!/usr/bin/env python3
"""@brief Codex CLI launcher with project-context auth file synchronization.

@details Ensures project-local Codex context is prepared before command
execution. The launcher copies auth state from `~/.codex/auth.json` into
`<project>/.codex/auth.json` before CLI launch, sets
`CODEX_HOME=<project>/.codex`, executes `codex --yolo`, then copies auth state
back from project path to home path before returning.
@satisfies REQ-014, REQ-043, REQ-044, REQ-064
"""

import os
import shutil
import subprocess
from pathlib import Path

from shell_scripts.utils import require_project_root, require_commands

## @var PROGRAM
#  @brief Base CLI program name used in help output.
#  @details Constant identifier for usage-line rendering in command help.
PROGRAM = "shellscripts"
## @var DESCRIPTION
#  @brief One-line command description for dispatcher help surfaces.
#  @details Exposed by command registry introspection (`get_all_commands`).
DESCRIPTION = "Launch OpenAI Codex CLI in the project context."


def print_help(version: str) -> None:
    """@brief Print command-specific help for `codex`.

    @details Emits usage and pass-through argument behavior for deterministic
    terminal rendering; does not mutate process state.
    @param version {str} CLI version string propagated by dispatcher.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """
    print(f"Usage: {PROGRAM} codex [args...] ({version})")
    print()
    print("codex options:")
    print("  All arguments are passed through to the Codex CLI.")
    print("  --help  - Show this help message.")


def _copy_auth_file(source_path: Path, destination_path: Path) -> None:
    """@brief Copy Codex auth file while replacing destination file or symlink.

    @details Ensures destination parent directory exists, removes an existing
    destination entry when it is a file or symbolic link, then copies source
    bytes to destination preserving metadata with `shutil.copy2`. Time
    complexity O(n) where n is auth file size.
    @param source_path {Path} Existing auth file source path.
    @param destination_path {Path} Auth file destination path to overwrite.
    @return {None} Applies destination filesystem mutation.
    @throws {OSError} If source read, destination unlink, or copy operation fails.
    @satisfies REQ-043, REQ-044
    """
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists() or destination_path.is_symlink():
        destination_path.unlink()
    shutil.copy2(source_path, destination_path)


def run(args: list[str]) -> int:
    """@brief Launch Codex CLI with project-scoped environment preparation.

    @details Resolves project root, copies auth from home into project auth
    file, sets `CODEX_HOME=<project-root>/.codex`, executes `codex --yolo` plus
    pass-through args through blocking subprocess run, then copies project auth
    back to home path in a `finally` block.
    @param args {list[str]} Additional CLI args forwarded to Codex.
    @return {int} Child process return code.
    @throws {OSError} Propagated for auth-file copy or process-launch failures.
    @satisfies REQ-014, REQ-043, REQ-044, REQ-064
    """
    project_root = require_project_root()
    project_auth_path = project_root / ".codex" / "auth.json"
    home_auth_path = Path.home() / ".codex" / "auth.json"
    _copy_auth_file(home_auth_path, project_auth_path)
    codex_home = str(project_root / ".codex")
    os.environ["CODEX_HOME"] = codex_home
    cmd = ["codex", "--yolo"] + args
    cmd[0] = require_commands(cmd[0])
    try:
        result = subprocess.run(cmd)
    finally:
        _copy_auth_file(project_auth_path, home_auth_path)
    return result.returncode
