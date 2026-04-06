#!/usr/bin/env python3
"""@brief Codex CLI launcher with project-context authentication-link guard.

@details Ensures project-local Codex context is prepared before command
execution. The launcher enforces auth-link presence in `<project>/.codex`,
sets `CODEX_HOME` to `<project>/.codex`, and executes `codex --yolo` through
blocking subprocess invocation.
@satisfies REQ-014, REQ-043, REQ-044, REQ-064
"""

import os
import subprocess
from pathlib import Path

from shell_scripts.utils import print_info, require_project_root, require_commands

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


def _is_expected_auth_link(link_path: Path, target_path: Path) -> bool:
    """@brief Determine whether auth link already targets expected home file.

    @details Evaluates symlink kind and resolved destination with
    `strict=False` to support not-yet-materialized target files.
    Time complexity O(1) excluding filesystem metadata lookup costs.
    @param link_path {Path} Candidate project-local auth link path.
    @param target_path {Path} Expected user-home auth file path.
    @return {bool} True only when `link_path` is symlink resolving to `target_path`.
    @satisfies REQ-043
    """
    if not link_path.is_symlink():
        return False
    return link_path.resolve(strict=False) == target_path.resolve(strict=False)


def _ensure_auth_symlink(project_root: Path) -> None:
    """@brief Ensure project Codex auth path is symlinked to user auth file.

    @details Computes `<project-root>/.codex/auth.json` and verifies it points
    to `~/.codex/auth.json`. If not compliant, creates parent directories,
    replaces existing path entry, creates expected symlink, and emits one info
    message announcing link creation. Time complexity O(1).
    @param project_root {Path} Git project root used by command runtime context.
    @return {None} Applies filesystem mutations when compliance is absent.
    @throws {OSError} If directory creation, unlink, or symlink creation fails.
    @satisfies REQ-043, REQ-044
    """
    link_path = project_root / ".codex" / "auth.json"
    target_path = Path.home() / ".codex" / "auth.json"
    if _is_expected_auth_link(link_path, target_path):
        return

    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(target_path)
    print_info(f"Created symlink: {link_path} -> {target_path}")


def run(args: list[str]) -> int:
    """@brief Launch Codex CLI with project-scoped environment preparation.

    @details Resolves project root, guarantees codex auth symlink compliance,
    sets `CODEX_HOME=<project-root>/.codex`, then executes `codex --yolo` plus
    pass-through args through blocking subprocess run.
    @param args {list[str]} Additional CLI args forwarded to Codex.
    @return {int} Child process return code.
    @throws {OSError} Propagated for filesystem or process-launch failures.
    @satisfies REQ-014, REQ-043, REQ-044, REQ-064
    """
    project_root = require_project_root()
    _ensure_auth_symlink(project_root)
    codex_home = str(project_root / ".codex")
    os.environ["CODEX_HOME"] = codex_home
    cmd = ["codex", "--yolo"] + args
    cmd[0] = require_commands(cmd[0])
    result = subprocess.run(cmd)
    return result.returncode
