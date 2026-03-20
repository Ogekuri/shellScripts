#!/usr/bin/env python3
"""@brief `req` bootstrap orchestrator for current/child project directories.

@details Applies cleanup and scaffold actions, then executes external `req`
installation arguments for selected target directories. Target selection mode is
current directory by default, first-level child directories with `--dirs`, or
all descendant directories with `--recursive`. Provider/static-check argument
lists are resolved from runtime config with hardcoded fallback defaults.
@satisfies PRJ-003, DES-008, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shell_scripts.config import get_req_profile
from shell_scripts.utils import print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Run useReq bootstrap on current or discovered directories."

DELETE_DIRS: tuple[str, ...] = (
    ".gemini/commands",
    ".gemini/skills",
    ".claude/commands",
    ".claude/agents",
    ".claude/skills",
    ".github/prompts",
    ".github/agents",
    ".github/skills",
    ".codex/prompts",
    ".codex/skills",
    ".kiro/prompts",
    ".kiro/agents",
    ".kiro/skills",
    ".opencode/agent",
    ".opencode/command",
    ".opencode/skill",
)

REQUIRED_DIRS: tuple[str, ...] = (
    "guidelines",
    "docs",
    "tests",
    "src",
    "scripts",
    ".github/workflows",
)


def _is_hidden_path(path: Path, base_dir: Path) -> bool:
    """@brief Determine whether path contains hidden segments below base.

    @details Computes relative parts from `base_dir` and returns `True` when any
    path segment starts with a dot-prefix, preventing accidental traversal of
    hidden metadata directories (for example `.git`).
    @param path {Path} Candidate directory path.
    @param base_dir {Path} Root directory used for relative-segment evaluation.
    @return {bool} `True` when candidate has hidden relative segments.
    @satisfies REQ-052, REQ-053
    """

    return any(part.startswith(".") for part in path.relative_to(base_dir).parts)


def print_help(version: str) -> None:
    """@brief Render command help for `req`.

    @details Prints selector options and behavior contract for target directory
    discovery and external `req` invocation flow.
    @param version {str} CLI version string appended in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """

    print(f"Usage: {PROGRAM} req [--dirs | --recursive] ({version})")
    print()
    print("req options:")
    print("  --dirs       - Target first-level child directories only.")
    print("  --recursive  - Target all descendant directories recursively.")
    print("  --help       - Show this help message.")


def _iter_first_level_dirs(base_dir: Path) -> list[Path]:
    """@brief Collect first-level child directories in deterministic order.

    @details Enumerates direct children of `base_dir`, keeps only directories,
    and sorts by path string for stable command behavior.
    @param base_dir {Path} Directory whose first-level children are listed.
    @return {list[Path]} Sorted first-level child directories.
    @satisfies REQ-052
    """

    return sorted(
        (
            entry
            for entry in base_dir.iterdir()
            if entry.is_dir() and not _is_hidden_path(entry, base_dir)
        ),
        key=str,
    )


def _iter_descendant_dirs(base_dir: Path) -> list[Path]:
    """@brief Collect descendant directories recursively in deterministic order.

    @details Traverses all descendants via glob expansion, excludes `base_dir`
    itself, keeps only directories, and sorts by path string.
    @param base_dir {Path} Directory whose descendants are listed.
    @return {list[Path]} Sorted descendant directory list excluding `base_dir`.
    @satisfies REQ-053
    """

    return sorted(
        (
            entry
            for entry in base_dir.rglob("*")
            if entry.is_dir() and not _is_hidden_path(entry, base_dir)
        ),
        key=str,
    )


def _build_req_args(target_dir: Path) -> list[str]:
    """@brief Build external `req` argument vector for one target directory.

    @details Uses hardcoded non-overridable arguments and appends repeated
    runtime-configured providers/static-check entries sourced from `get_req_profile`.
    @param target_dir {Path} Target directory used to parameterize path flags.
    @return {list[str]} External `req` argv vector.
    @satisfies REQ-049, REQ-050
    """

    providers, static_checks = get_req_profile()
    args = [
        "req",
        "--base",
        str(target_dir),
        "--docs-dir",
        str(target_dir / "docs"),
        "--guidelines-dir",
        str(target_dir / "guidelines"),
        "--src-dir",
        str(target_dir / "src"),
        "--src-dir",
        str(target_dir / "scripts"),
        "--src-dir",
        str(target_dir / ".github/workflows"),
        "--tests-dir",
        str(target_dir / "tests"),
    ]
    for provider in providers:
        args.extend(["--provider", provider])
    args.append("--upgrade-guidelines")
    for static_check in static_checks:
        args.extend(["--enable-static-check", static_check])
    return args


def _prepare_target_directory(target_dir: Path) -> None:
    """@brief Apply cleanup and scaffold operations for one target directory.

    @details Removes each predefined integration directory if present and
    ensures required project subdirectories exist before external `req` call.
    @param target_dir {Path} Target directory to mutate.
    @return {None} Performs filesystem side effects.
    @satisfies REQ-048
    """

    for rel_path in DELETE_DIRS:
        shutil.rmtree(target_dir / rel_path, ignore_errors=True)
    for rel_path in REQUIRED_DIRS:
        (target_dir / rel_path).mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> int:
    """@brief Execute `req` orchestration for selected directory targets.

    @details Parses mutually exclusive selector options, resolves target set,
    applies cleanup/scaffold phase, and executes external `req` for each target.
    Returns `1` on invalid option combinations or unknown options. Converts
    external `req` non-zero exits into explicit error output and propagated
    return codes.
    @param args {list[str]} Command arguments excluding `req` token.
    @return {int} `0` on success; non-zero for option or subprocess failures.
    @exception {subprocess.CalledProcessError} Internally handled and converted
      to deterministic return code + error output.
    @satisfies REQ-048, REQ-049, REQ-051, REQ-052, REQ-053, REQ-054
    """

    mode_current = True
    mode_dirs = False
    mode_recursive = False

    for arg in args:
        if arg == "--dirs":
            mode_dirs = True
            mode_current = False
        elif arg == "--recursive":
            mode_recursive = True
            mode_current = False
        else:
            print_error(f"Unknown option: {arg}")
            return 1

    if mode_dirs and mode_recursive:
        print_error("Options --dirs and --recursive are mutually exclusive.")
        return 1

    base_dir = Path.cwd()
    if mode_current:
        targets = [base_dir]
    elif mode_dirs:
        targets = _iter_first_level_dirs(base_dir)
    else:
        targets = _iter_descendant_dirs(base_dir)

    print("-----------------------------------------------------------------------------------------------------------------")
    print("Clean previous install")
    print("-----------------------------------------------------------------------------------------------------------------")
    for target_dir in targets:
        _prepare_target_directory(target_dir)
        print()

    for target_dir in targets:
        print("-----------------------------------------------------------------------------------------------------------------")
        print(f"Install useReq: {target_dir}")
        print("-----------------------------------------------------------------------------------------------------------------")
        if not target_dir.is_dir():
            print_error(f"Path does not exist: {target_dir}")
            return 1
        try:
            subprocess.run(_build_req_args(target_dir), check=True)
        except subprocess.CalledProcessError as exc:
            print_error(f"req failed for {target_dir} with exit code {exc.returncode}.")
            return int(exc.returncode)
        print("-----------------------------------------------------------------------------------------------------------------")
        print()

    return 0
