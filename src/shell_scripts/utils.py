#!/usr/bin/env python3
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


def is_linux():
    return sys.platform.startswith("linux")


def command_exists(cmd):
    return shutil.which(cmd) is not None


def require_commands(*cmds):
    missing = [cmd for cmd in cmds if not command_exists(cmd)]
    if missing:
        print_error(f"Missing required dependencies: {', '.join(missing)}")
        sys.exit(1)


def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)
