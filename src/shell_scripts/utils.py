#!/usr/bin/env python3
"""@brief Shared CLI utility helpers for platform, subprocess, and output handling.

@details Provides reusable terminal formatting utilities, project-root
resolution, platform detection with runtime OS caching, command availability
checks, and thin subprocess wrappers used across command modules.
@satisfies CTN-003, CTN-005, DES-002, REQ-047
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

## @var _RUNTIME_OS
#  @brief Cached normalized runtime operating-system token.
#  @details Initialized on first detection and reused to guarantee stable
#  startup-level OS semantics across command execution flow.
#  @satisfies DES-002, REQ-047
_RUNTIME_OS = None


def color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def c(text, color):
    if color_enabled():
        return f"{color}{text}{RESET}"
    return str(text)


def print_info(msg):
    print(c(f"[INFO] {msg}", BRIGHT_BLUE + BOLD))


def print_error(msg):
    print(c(f"[ERROR] {msg}", BRIGHT_RED + BOLD), file=sys.stderr)


def print_warn(msg):
    print(c(f"[WARN] {msg}", BRIGHT_YELLOW + BOLD), file=sys.stderr)


def print_success(msg):
    print(c(f"[OK] {msg}", BRIGHT_GREEN + BOLD))


def get_project_root():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def require_project_root():
    root = get_project_root()
    if root is None:
        print_error("Cannot determine the project root. Are you inside a git repository?")
        sys.exit(1)
    return root


def detect_runtime_os():
    """@brief Detect and cache runtime operating-system token.

    @details Normalizes `sys.platform` into deterministic categories
    (`windows`, `linux`, `darwin`, `other`) and stores the result in module
    cache for subsequent calls. Time complexity O(1).
    @return {str} Normalized runtime operating-system token.
    @satisfies DES-002, REQ-047
    """

    global _RUNTIME_OS
    platform_token = sys.platform.lower()
    if platform_token.startswith("win"):
        _RUNTIME_OS = "windows"
    elif platform_token.startswith("linux"):
        _RUNTIME_OS = "linux"
    elif platform_token.startswith("darwin"):
        _RUNTIME_OS = "darwin"
    else:
        _RUNTIME_OS = "other"
    return _RUNTIME_OS


def get_runtime_os():
    """@brief Return cached runtime operating-system token.

    @details Lazily initializes the cache via `detect_runtime_os` when unset,
    preserving a single startup-consistent OS classification.
    @return {str} Normalized runtime operating-system token.
    @satisfies DES-002, REQ-047
    """

    if _RUNTIME_OS is None:
        return detect_runtime_os()
    return _RUNTIME_OS


def is_windows():
    """@brief Check whether runtime operating system is Windows.

    @details Evaluates cached runtime token from `get_runtime_os`.
    @return {bool} `True` when runtime OS is Windows; otherwise `False`.
    @satisfies DES-013, REQ-008, REQ-047
    """

    return get_runtime_os() == "windows"


def is_linux():
    """@brief Check whether runtime operating system is Linux.

    @details Evaluates cached runtime token from `get_runtime_os`.
    @return {bool} `True` when runtime OS is Linux; otherwise `False`.
    @satisfies CTN-004, REQ-004, REQ-005, REQ-047
    """

    return get_runtime_os() == "linux"


def command_exists(cmd):
    return shutil.which(cmd) is not None


def require_commands(*cmds):
    missing = [cmd for cmd in cmds if not command_exists(cmd)]
    if missing:
        print_error(f"Missing required dependencies: {', '.join(missing)}")
        sys.exit(1)


def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)
